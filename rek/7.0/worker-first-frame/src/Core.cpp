#include "DB.h"
#include <boost/foreach.hpp>
#include <boost/date_time/posix_time/ptime.hpp>
#include <boost/date_time/posix_time/posix_time_io.hpp>
#include <boost/format.hpp>
#include <boost/algorithm/string.hpp>
#include <glog/logging.h>
#include <ctime>
#include <cstdlib>
#include <sstream>
#include <mongo/util/version.h>
#include <mongo/bson/bsonobjbuilder.h>


#include "Core.h"
#include "FrameTemplate.h"
#include "utils/base64.h"
#include "utils/benchmark.h"
#include <mongo/bson/bsonobjbuilder.h>


using std::list;
using std::vector;
using std::map;
using std::unique_ptr;
using std::string;
using namespace boost::posix_time;
#define foreach	BOOST_FOREACH

int Core::request_processed_ = 0;

Core::Core()
{
    LoadAllEntities();
}

Core::~Core()
{
}


/** Обработка запроса на показ рекламы с параметрами ``params``.
 */
std::string Core::Process(const Params &params)
{
    ProcessMQ();
    Informer informer(params.informer_);
	if (!informer.valid()) {
		RequestDebugInfo(params);
	    return std::string();
    }
    std::string inf;
    try{
        inf = informer.domain();
        LOG(INFO) << inf;
        std::replace(inf.begin(), inf.end(), '.', '_');
        std::replace(inf.begin(), inf.end(), '/', '_');
        LOG(INFO) << inf;
    }
    catch (std::exception const &ex)
    {
        inf = informer.domain();
        LOG(ERROR) << "exception " << typeid(ex).name() << ": " << ex.what();
    }
    frame_query = params.query_;
    frame_html = boost::str(boost::format(FrameTemplate::instance()->getFrameTemplate())
                % inf
                % frame_query
                % informer.width()
                % informer.height()
                % params.cookie_name_
                % params.cookie_domain_);
	return frame_html;
}

/** Проверка и обработка сообщений MQ.

    Проверяются сообщения со следующими routing key:

    <table>
    <tr>
        <td> \c advertise.# </td>
        <td> уведомления об изменениях в рекламных кампаниях; </td>
    </tr>
    <tr>
        <td> \c informer.# </td>
        <td> уведомления об изменениях в информерах; </td>
    </tr>
    <tr>
	    <td> \c account.# </td>
        <td> уведомления об изменениях в аккаунтах getmyad. </td>
    </tr>
    </table>
	
    На данный момент при получении сообщений \c account.# происходит полная
    перезагрузка всех сущностей (фактически, рестарт). Если это когда-нибудь
    станет узким местом, можно сделать более "тонкую" обработку.

    При получении сообщений \c advertise.# и \c informer.# перезагружено
    будет только то, что нужно (конкретная кампания или информер.

    Чтобы не грузить RabbitMQ лишними проверками, реальное обращение происходит
    не чаще одного раза в две секунды. Во избежание подвисания сервиса в
    случае, когда шлётся сразу много сообщения, после обработки сообщения
    сервис две секунды работает на обработку запросов и не проверяет новые
    сообщения.

    Если при проверке сообщений произошла ошибка (например, RabbitMq оказался
    недоступен) интервал между проверками постепенно увеличивается до пяти
    минут.
*/
bool Core::ProcessMQ()
{
    // Интервал (в секундах) между проверками MQ
    static int check_interval = 0;

    // При возникновении ошибки check_interval постепенно увеличивается до
    // max_check_interval с шагом interval_delta
    const int max_check_interval = 5 * 60;
    const int interval_delta = 5;

    if (!amqp_initialized_)
        return false;
    if (!time_last_mq_check_.is_not_a_date_time() &&
        ((second_clock::local_time() - time_last_mq_check_) <
            seconds(check_interval)))
        return false;
    time_last_mq_check_ = second_clock::local_time();
    if (amqp_down_)
        InitMessageQueue();

    try {
        { // Проверка сообщений informer.#
            mq_informer_->Get(AMQP_NOACK);
            AMQPMessage *m = mq_informer_->getMessage();
            if (m->getMessageCount() > -1) {
                LOG(INFO) << "Message retrieved:";
                LOG(INFO) << "  body:        " << m->getMessage();
                LOG(INFO) << "  routing key: " <<  m->getRoutingKey();
                LOG(INFO) << "  exchange:    " <<  m->getExchange();
                Informer informer(m->getMessage());
                string logline = boost::str(
                        boost::format("Message (key=%1%, body=%2%, "
                                      "informer=%3%)")
                        % m->getRoutingKey()
                        % m->getMessage()
                        % informer.title());
                LogToAmqp(logline);
                Benchmark bench("Informer reloaded");
                Informer::loadInformer(informer);
                time_last_mq_check_ = second_clock::local_time();
                check_interval = 2;
                return true;
            }
        }
        { // Проверка сообщений account.#
            mq_account_->Get(AMQP_NOACK);
            AMQPMessage *m = mq_account_->getMessage();
            if (m->getMessageCount() > -1) {
                LOG(INFO) << "Message retrieved:";
                LOG(INFO) << "  body:        " << m->getMessage();
                LOG(INFO) << "  routing key: " <<  m->getRoutingKey();
                LOG(INFO) << "  exchange:    " <<  m->getExchange();
                string logline = boost::str(
                        boost::format("Message (key=%1%, body=%2%")
                        % m->getRoutingKey()
                        % m->getMessage());
                LogToAmqp(logline);
                LoadAllEntities();
                time_last_mq_check_ = second_clock::local_time();
                check_interval = 2;
                return true;
            }
        }
        check_interval = 2;
        amqp_down_ = false;
    } catch (AMQPException &ex) {
        if (!amqp_down_)
            LogToAmqp("AMQP is down");
        amqp_down_ = true;
        if (check_interval + interval_delta < max_check_interval)
            check_interval += interval_delta;
        LOG(ERROR) << ex.getMessage();
    }
    return false;
}


/*
*  Загружает из основной базы данных следующие сущности:
*
*  - рекламные предложения;
*  - рекламные кампании;
*  - информеры.
*
*  Если в кампании нет рекламных предложений, она будет пропущена.
*/
void Core::LoadAllEntities()
{
    Benchmark bench("All entities reloaded");

    Informer::loadAll();
	//LOG(INFO) << "Загрузили все информеры.\n";

}


/** \brief  Инициализация очереди сообщений (AMQP).

    Если во время инициализации произошла какая-либо ошибка, то сервис
    продолжит работу, но возможность оповещения об изменениях и горячего
    обновления будет отключена.
*/
void Core::InitMessageQueue()
{
    try {
	// Объявляем точку обмена
	amqp_ = new AMQP("guest:guest@localhost//");
	exchange_ = amqp_->createExchange();
	exchange_->Declare("getmyad", "topic", AMQP_AUTODELETE);
	LogToAmqp("AMQP is up");

	// Составляем уникальные имена для очередей
	ptime now = microsec_clock::local_time();
	std::string postfix = to_iso_string(now);
	boost::replace_first(postfix, ".", ",");
	std::string mq_informer_name( "getmyad.informer." + postfix );
	std::string mq_account_name( "getmyad.account." + postfix );

	// Объявляем очереди
	mq_informer_ = amqp_->createQueue();
	mq_informer_->Declare(mq_informer_name, AMQP_AUTODELETE | AMQP_EXCLUSIVE);
	mq_account_ = amqp_->createQueue();
	mq_account_->Declare(mq_account_name, AMQP_AUTODELETE | AMQP_EXCLUSIVE);

	// Привязываем очереди
	exchange_->Bind(mq_informer_name, "informer.#");
	exchange_->Bind(mq_account_name, "account.#");

	amqp_initialized_ = true;
	amqp_down_ = false;

	LOG(INFO) << "Created ampq queues: " <<
		mq_informer_name <<  ", " <<
		mq_account_name;
	LogToAmqp("Created amqp queue " + mq_informer_name);
	LogToAmqp("Created amqp queue " + mq_account_name);

    } catch (AMQPException &ex) {
	LOG(ERROR) << ex.getMessage();
	LOG(ERROR) << "Error in AMPQ init. Feature will be disabled.";
	LogToAmqp("Error in AMQP init: " + ex.getMessage());
	amqp_initialized_ = false;
	amqp_down_ = true;
    }
}


/** Возвращает данные о состоянии службы
 *  TODO Надоб переписать с учётом использования boost::formater красивее будет как некак :)
 */
std::string Core::Status()
{
    // Обработано запросов на момент прошлого обращения к статистике
    static int last_time_request_processed = 0;

    // Время последнего обращения к статистике
    static ptime last_time_accessed;

    time_duration d;

    // Вычисляем количество запросов в секунду
    if (last_time_accessed.is_not_a_date_time())
	last_time_accessed = time_service_started_;
    ptime now = microsec_clock::local_time();
    int millisecs_since_last_access =
	    (now - last_time_accessed).total_milliseconds();
    int millisecs_since_start =
	    (now - time_service_started_).total_milliseconds();
    int requests_per_second_current = 0;
    int requests_per_second_average = 0;
    if (millisecs_since_last_access)
	requests_per_second_current =
		(request_processed_ - last_time_request_processed) * 1000 /
		millisecs_since_last_access;
    if (millisecs_since_start)
	requests_per_second_average = request_processed_ * 1000 /
				      millisecs_since_start;

    last_time_accessed = now;
    last_time_request_processed = request_processed_;

    std::stringstream out;
    out << "<html>\n"
	    "<head><meta http-equiv=\"content-type\" content=\"text/html; "
	    "charset=UTF-8\">\n"
	    "<style>\n"
	    "body { font-family: Arial, Helvetica, sans-serif; }\n"
	    "h1, h2, h3 {font-family: \"georgia\", serif; font-weight: 400;}\n"
	    "table { border-collapse: collapse; border: 1px solid gray; }\n"
	    "td { border: 1px dotted gray; padding: 5px; font-size: 10pt; }\n"
	    "th {border: 1px solid gray; padding: 8px; font-size: 10pt; }\n"
	    "</style>\n"
	    "</head>"
	    "<body>\n<h1>Состояние службы Yottos GetMyAd worker</h1>\n"
	    "<table>"
	    "<tr>"
	    "<td>Обработано запросов:</td> <td><b>" << request_processed_ <<
	    "</b> (" << requests_per_second_current << "/сек, "
	    " в среднем " << requests_per_second_average << "/сек) "
	    "</td></tr>\n";

    out << "<tr><td>Имя сервера: </td> <td>" <<
	    (getenv("SERVER_NAME")? getenv("SERVER_NAME"): "неизвестно") <<
	    "</td></tr>\n";
    out << "<tr><td>IP сервера: </td> <td>" <<
	    (server_ip_.empty()? "неизвестно": server_ip_) <<
	    "</td></tr>\n";
    out << "<tr><td>Текущее время: </td> <td>" <<
	    second_clock::local_time() <<
	    "</td></tr>\n";

    try {
	mongo::DB db_main;
	out << "<tr><td>Основная база данных:</td> <td>" <<
		db_main.server_host() << "/" << db_main.database() << "<br/>";
	out << "slave_ok = " << (db_main.slave_ok()? "true" : "false");
	if (db_main.replica_set().empty())
	    out << " (no replica set)";
	else
	    out << " (replSet=" << db_main.replica_set() << ")";
	out << "</td></tr>\n";
    } catch (mongo::DB::NotRegistered &) {
	out << "Основная база не определена</td></tr>\n";
    }

    out << "<tr><td>Время запуска:</td> <td>" << time_service_started_ <<
	    "</td></tr>" <<
	    "<tr><td>AMQP:</td><td>" <<
	    (amqp_initialized_ && !amqp_down_? "активен" : "не активен") <<
	    "</td></tr>\n";
    out <<  "<tr><td>Сборка: </td><td>" << __DATE__ << " " << __TIME__ <<
	    "</td></tr>";
    out <<  "<tr><td>Драйвер mongo: </td><td>" << mongo::versionString <<
	    "</td></tr>";
    out << "</table>\n";

    // Журнал сообщений AMQP
    out << "<p>Журнал AMQP: </p>\n"
	    "<table>\n";
    int i = 0;
    for (auto it = mq_log_.begin(); it != mq_log_.end(); it++)
	out << "<tr><td>" << ++i << "</td>"
		"<td>" << *it << "</td></tr>\n";
    out << "<tr><td></td><td>Последняя проверка сообщений: " <<
	    time_last_mq_check_ << "</td><tr>\n"
	    "</table>\n";

    out << "</body>\n</html>\n";

    return out.str();
}


/** Возвращает отладочную информацию про текущий запрос */
std::string Core::RequestDebugInfo(const Params &params) const
{
    std::ostringstream out;
    out << "ip: " << params.ip_ << ", "
	    "inf: " << params.informer_;
    return out.str();
}


/** Помещает сообщение \a message в журнал AMQP */
void Core::LogToAmqp(const std::string &message)
{
    string logline = boost::str(
	    boost::format("%1% \t %2%")
	    % second_clock::local_time()
	    % message);
    mq_log_.push_back(logline);
}
