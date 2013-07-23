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

#include "Core.h"
#include "InformerTemplate.h"
#include "utils/base64.h"
#include "utils/benchmark.h"


using std::list;
using std::vector;
using std::map;
using std::unique_ptr;
using namespace boost::posix_time;
#define foreach	BOOST_FOREACH

int Core::request_processed_ = 0;

Core::Core()
    : amqp_initialized_(false), amqp_down_(true), amqp_(0),
    redirect_script_("/redirect")
{
    LoadAllEntities();
    InitMessageQueue();
    InitMongoDB();
    time_service_started_ = second_clock::local_time();
}

Core::~Core()
{
    delete amqp_;
}

/** Функтор генерирует токен для предложения ``offer``.
    Возвращает структуру Core::ImpressionItem.

    Токен представляет собой некое уникальное значение, введенное для
    избежания накруток (см. документацию).

    В тестовом режиме токеном является строка "test".
*/
class GenerateToken {
    Core::Params params_;
public:
    GenerateToken(const Core::Params &params) : params_(params) { }
    Core::ImpressionItem operator ()(const Offer &offer)
    {
	Core::ImpressionItem result(offer);

	// Генерируем токен
	if (params_.test_mode_)
	    result.token = "test";
	else {
	    std::ostringstream s;
	    s << std::hex << rand(); // Cлучайное число в шестнадцатиричном
	    result.token = s.str();  // исчислении
	}
	return result;
    }
};


/** Функтор составляет ссылку перенаправления на предложение item.

    Вся строка запроса кодируется в base64 и после распаковки содержит
    следующие параметры:

    \param id        guid рекламного предложения
    \param inf       guid информера, с которого осуществляется переход
    \param url       ссылка, ведущая на товарное предложение
    \param server    адрес сервера, выдавшего ссылку
    \param token     токен для проверки действительности перехода
    \param loc	      адрес страницы, на которой показывается информер
    \param ref	      адрес страницы, откуда пришёл посетитель

    Пары (параметр=значение) разделяются символом \c '\\n' (перевод строки).
    Значения никак не экранируются, считается, что они не должны содержать
    символа-разделителя \c '\\n'.
*/
class GenerateRedirectLink {
    Informer informer_;
    string server_ip_;
    string redirect_script_;
    string location_;
    string referrer_;
public:
    GenerateRedirectLink(const Informer &informer,
			 const string &server_ip,
			 const string &redirect_script,
			 const string &location,
			 const string &referrer)
			     : informer_(informer), server_ip_(server_ip),
			     redirect_script_(redirect_script),
			     location_(location), referrer_(referrer) { }

    void operator ()(Core::ImpressionItem &item) {
	string query = boost::str(
		boost::format("id=%s\ninf=%s\ntoken=%s\nurl=%s\nserver=%s"
			      "\nloc=%s\nref=%s")
		% item.offer.id()
		% informer_.id()
		% item.token
		% item.offer.url()
		% server_ip_
		% location_
		% referrer_
		);
	item.redirect_url = redirect_script_ + "?" + base64_encode(query);
    }
};

std::string Core::Process(const Core::Params &params)
{
    request_processed_++;
    time_request_started_ = microsec_clock::local_time();

    ProcessMQ();

    Informer informer(params.informer_);
    if (!informer.valid()) {
	LOG(INFO) << "Invalid informer, returning void. " <<
		RequestDebugInfo(params);
	return std::string();
    }

    // Предложения, которые нужно показать
    vector<Offer> offers = getOffers(informer.capacity(), params);

    // Если нужно показать только социальную рекламу, а настройках стоит
    // опция "В случае отсутствия релевантной рекламы показывать
    // пользовательский код", то возвращаем пользовательскую заглушку
    if (informer.nonrelevant() == Informer::Show_UserCode && !params.json_) {
	bool all_social = true;
    	for (auto it = offers.begin(); it != offers.end(); it++)  {
	    if (!Campaign(it->campaign_id()).social()) {
		all_social = false;
		break;
    	    }
	}
	if (all_social)
	    return informer.user_code();
    }

    // Каждому элементу просмотра присваиваем уникальный токен
    vector<ImpressionItem> items;
    GenerateToken token_generator(params);
    std::transform(offers.begin(), offers.end(), back_inserter(items),
		   token_generator);

    // Составляем ссылку перенаправления для каждого элемента
    GenerateRedirectLink redirect_generator(informer, server_ip(),
					    redirect_script(),
					    params.location_,
					    params.referrer_);
    std::for_each(items.begin(), items.end(), redirect_generator);

    // Сохраняем выданные ссылки в базе данных
    try {
	markAsShown(items, params);
    } catch (mongo::DBException &ex) {
	LOG(ERROR) << "DBException during markAsShown(): " << ex.what();
    }

    // Возвращаем отформатированный информер
    if (params.json_)
	return OffersToJson(items);
    else
	return OffersToHtml(items, params);
}



/** 
    Алгоритм работы таков:

	-#  Получаем рекламные кампании, которые нужно показать в этот раз.
	    Выбор кампаний происходит случайно, но с учётом веса. На данный момент
        вес всех кампаний одинаков. Со временем можно сделать составной вес,
        который включал бы в себя цену за клик, CTR и т.д. (расчёт веса
        предварительно производится внешним скриптом).
        .
	-#  Для каждого "места", которое должно быть занято определённой
	    кампанией (п. 1) выбираем товар из этой кампании. Товар также
	    выбирается случайно, но с учётом веса, включающего в себя CTR и др.
	    (также расчитывается внешним скриптом). На данный момент все товары
        равны.
        .
	-#  При малом кол-ве предложений случайное распределение может давать
	    одинаковые элементы в пределах одного информера. Поэтому после
	    получения предложения на п.2, мы проверяем его на уникальность в
	    пределах информера, и если элемент является дубликатом,
	    предпринимаем ещё одну попытку получить предложение. Во избежание
	    вечных циклов, количество попыток ограничивается константой
	    \c Remove_Duplicates_Retries. Увеличение этой константы ведёт к
	    уменьшению вероятности попадания дубликатов, но увеличивает
	    время выполнения. Кроме того, удаление дубликатов меняет
	    весовое распределение предложений. \n
        .
        Иногда удалять дубликаты предложений в пределах кампании недостаточно.
        Например, мы должны показать две кампании. Первая из них содержит всего
        одно предолжение, вторая -- сто. Может случиться, что три места на
        информере будут принадлежать первой кампании. Понятно, что сколько бы
        попыток выбрать "другой" товар этой кампании, у нас ничего не выйдет
        и возникнет дубликат. Поэтому, после \c Remove_Duplicates_Retries
        попыток выбора предложения будет выбрана другая кампания, и цикл
        повториться. Количество возможных смен кампаний задаётся константой
        \c Change_Campaign_Retries.
        .
	-#  Предложения, указанные в \c params.exluded_offers, по возможности
	    исключаются из просмотра. Это используется в прокрутке информера.
 */
vector<Offer> Core::getOffers(int count, const Core::Params &params)
{
    vector<Offer> result(count, Offer(""));

    if (!count) {
        LOG(WARNING) << "0 offers requested!";
        return result;
    }

    list<Campaign> camps;
    getCampaigns(params, camps);

    RandomEntity<Campaign> random_campaigns;
    for (auto it = camps.begin(); it != camps.end(); it++) {
        if (!Offers::x()->offers_by_campaign(*it).empty())
            random_campaigns.add(*it, 1);
    }

    try {
        for (int i = 0; i < count; i++)
            result[i] = 
                _get_one_offer(result, random_campaigns,
                               params.excluded_offers_);

    } catch (RandomEntity<Offer>::NoItemsException) {
        LOG(WARNING) << "RandomEntity<Offer>::NoItemsException. "
                     << RequestDebugInfo(params);
        return result;
    } catch (RandomEntity<Campaign>::NoItemsException) {
        LOG(WARNING) << "RandomEntity<Campaign>::NoItemsException. "
                     << RequestDebugInfo(params);
        return result;
    }

    return result;
}


/** Возвращает одно предложение, которое можно добавить к результату */
Offer Core::_get_one_offer(const vector<Offer> &result,
                           RandomEntity<Campaign> &random_campaigns,
                           const vector<string> &excluded_offers)
{
    const int Remove_Duplicates_Retries = 5;
    const int Change_Campaign_Retries = 7;
    Offer offer("");
    bool duplicate = true;              // Является ли дупликатом
    int campaign_retry = 0;             // Номер попытки смены кампании

    while (++campaign_retry <= Change_Campaign_Retries && duplicate) {
        Campaign c = random_campaigns.get();
        RandomEntity<Offer> offers = offers_by_campaign(c);
    
        // Удаляем исключённые элементы из списка показа
        for (auto it = excluded_offers.begin();
                  it != excluded_offers.end(); it++) {
            offers.remove(Offer(*it));
        }
        if (!offers.count()) {
            random_campaigns.remove(c);
            continue;
        }
    
        int retry = 0;         // Номер попытки
        do {
            offer = offers.get();
            duplicate = (find(result.begin(), result.end(), offer) !=
                         result.end());
        } while (duplicate && ++retry < Remove_Duplicates_Retries);
    }
    return offer;
}

/** Возвращает в параметре \a out_campaigns список кампаний, подходящих под
    параметры \a params. */
void Core::getCampaigns(const Core::Params &params,
			list<Campaign> &out_campaigns) const
{
    Rules rules;
    rules.set_ip(params.ip_);
    rules.set_informer(params.informer_);
    rules.set_time(params.time_);
    if (!params.country_.empty())
	rules.set_country(params.country_);
    if (!params.region_.empty())
	rules.set_region(params.region_);
    out_campaigns = rules.campaigns();
}



/** Возвращает генератор предложений для кампании campaign,
    кеширует результат.
 */
RandomEntity<Offer> &Core::offers_by_campaign(const Campaign &campaign)
{
    map<Campaign, RandomEntity<Offer> >::iterator it =
	    offers_by_campaign_.find(campaign);
    if (it != offers_by_campaign_.end())
	return it->second;

    // TODO: Весовые распределения товаров
    RandomEntity<Offer> result;
    list<Offer> offers = Offers::x()->offers_by_campaign(campaign);
    foreach ( Offer &offer, offers )
	result.add(offer, 1);

    offers_by_campaign_[campaign] = result;	    // Кешируем результат
    return offers_by_campaign_[campaign];
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
        { // Проверка сообщений advertise.#
            mq_campaign_->Get(AMQP_NOACK);
            AMQPMessage *m = mq_campaign_->getMessage();
            if (m->getMessageCount() > -1) {
                LOG(INFO) << "Message retrieved:";
                LOG(INFO) << "  body:        " << m->getMessage();
                LOG(INFO) << "  routing key: " <<  m->getRoutingKey();
                LOG(INFO) << "  exchange:    " <<  m->getExchange();
                Campaign campaign = Campaign(m->getMessage());
                string logline = boost::str(
                        boost::format("Message (key=%1%, body=%2%, "
                                      "campaign=%3%)")
                        % m->getRoutingKey()
                        % m->getMessage()
                        % campaign.title());
                LogToAmqp(logline);
                ReloadCampaign(campaign);
                time_last_mq_check_ = second_clock::local_time();
                check_interval = 2;
                return true;
            }
        }
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

    Campaign::loadAll();
    Offers::x()->loadFromDatabase();
    Informer::loadAll();

    // Проверяем, нет ли кампаний с 0 предложений
    auto campaigns = Campaign::all();
    for (auto it = campaigns.begin(); it != campaigns.end(); it++)
	if (Offers::x()->offers_by_campaign(*it).empty())
	    LOG(WARNING) << "В кампании " << it->title() << " нет предложений!";

    // Сбрасываем кеш
    offers_by_campaign_.clear();
}


void Core::ReloadCampaign(const Campaign &campaign)
{
    Benchmark bench("Campaign " + campaign.title() + " reloaded");
    Campaign::loadAll();
    Offers::x()->loadByCampaign(campaign);
    offers_by_campaign_.clear();
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
	amqp_ = new AMQP;
	exchange_ = amqp_->createExchange();
	exchange_->Declare("getmyad", "topic", AMQP_AUTODELETE);
	LogToAmqp("AMQP is up");

	// Составляем уникальные имена для очередей
	ptime now = microsec_clock::local_time();
	std::string postfix = to_iso_string(now);
	boost::replace_first(postfix, ".", ",");
	std::string mq_advertise_name( "getmyad.advertise." + postfix );
	std::string mq_informer_name( "getmyad.informer." + postfix );
	std::string mq_account_name( "getmyad.account." + postfix );

	// Объявляем очереди
	mq_campaign_ = amqp_->createQueue();
	mq_campaign_->Declare(mq_advertise_name, AMQP_AUTODELETE | AMQP_EXCLUSIVE);
	mq_informer_ = amqp_->createQueue();
	mq_informer_->Declare(mq_informer_name, AMQP_AUTODELETE | AMQP_EXCLUSIVE);
	mq_account_ = amqp_->createQueue();
	mq_account_->Declare(mq_account_name, AMQP_AUTODELETE | AMQP_EXCLUSIVE);

	// Привязываем очереди
	exchange_->Bind(mq_advertise_name, "campaign.#");
	exchange_->Bind(mq_informer_name, "informer.#");
	exchange_->Bind(mq_account_name, "account.#");

	amqp_initialized_ = true;
	amqp_down_ = false;

	LOG(INFO) << "Created ampq queues: " <<
		mq_advertise_name << ", " <<
		mq_informer_name <<  ", " <<
		mq_account_name;
	LogToAmqp("Created amqp queue " + mq_advertise_name);
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



/** Подготовка базы данных MongoDB.
*/
void Core::InitMongoDB()
{
    mongo::DB db("log");
    const int K = 1000;
    const int M = 1000 * K;
    db.createCollection("log.impressions", 250*M, true, 1*M);
}


/** Добавляет в журнал просмотров log.impressions предложения \a items.
    Если показ информера осуществляется в тестовом режиме, запись не происходит.

    Внимание: Используется база данных, зарегистрированная под именем 'log'.
 */
void Core::markAsShown(const vector<ImpressionItem> &items,
		       const Core::Params &params)
{
    if (params.test_mode_)
	return;
    mongo::DB db("log");
    int count = 0;
    BOOST_FOREACH (const ImpressionItem &i, items) {

	std::tm dt_tm;
	dt_tm = boost::posix_time::to_tm(params.time_);
	mongo::Date_t dt( (mktime(&dt_tm)) * 1000LLU);
	Campaign campaign(i.offer.campaign_id());

	auto record = BSON(
		"dt" << dt <<
		"id" << i.offer.id() <<
		"title" << i.offer.title() <<
		"inf" << params.informer_ <<
		"ip" << params.ip_ <<
		"social" << !(campaign.valid() && !campaign.social()) <<
		"token" << i.token
		);

	db.insert("log.impressions", record, true);
	count++;
    }
    LOG_IF(WARNING, count == 0 ) << "No items was added to log.impressions!";
}


/** Возвращает данные о состоянии службы */
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

    try {
	mongo::DB db_log("log");
	out << "<tr><td>База данных журналирования: </td> <td>" <<
		db_log.server_host() << "/" << db_log.database() << "<br/>";
	out << "slave_ok = " << (db_log.slave_ok()? "true" : "false");
	if (db_log.replica_set().empty())
	    out << " (no replica set)";
	else
	    out << " (replSet=" << db_log.replica_set() << ")";
	out << "</td></tr>";

    } catch (mongo::DB::NotRegistered &) {
	out << "База данных журналирования не определена</td></tr>\n";
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

    std::list<Campaign> campaigns = Campaign::all();
    out << "<p>Загружено <b>" << campaigns.size() << "</b> кампаний: </p>\n";
    out << "<table><tr>\n"
	    "<th>Наименование</th>"
	    "<th>Действительна</th>"
	    "<th>Социальная</th>"
	    "<th>Предложений</th>"
	    "</tr>\n";
    for (auto it = campaigns.begin(); it != campaigns.end(); it++) {
	Campaign c(*it);
	out << "<tr>" <<
		"<td>" << c.title() << "</td>" <<
		"<td>" << (c.valid()? "Да" : "Нет") << "</td>" <<
		"<td>" << (c.social()? "Да" : "Нет") << "</td>" <<
		"<td>" << Offers::x()->offers_by_campaign(c).size() << "</td>"<<
		"</tr>\n";
    }
    out << "</table>\n\n";

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


std::string Core::OffersToHtml(const std::vector<ImpressionItem> &items,
			       const Core::Params &params) const
{
    Informer informer(params.informer_);

    // URL получения следующей порции предложений (TODO: Применять UrlEncode)
    stringstream url;
    url << params.script_name_ <<
	    "?scr=" << params.informer_ <<
	    "&show=json";
    if (params.test_mode_)
	url << "&test=true";
    if (!params.country_.empty())
	url << "&country=" << params.country_;
    if (!params.region_.empty())
	url << "&region=" << params.region_;
    url << "&";

    // Получаем HTML-код информера
    std::string informer_html =
	    boost::str(boost::format(InformerTemplate())
	       % informer.css()
	       % OffersToJson(items)
	       % informer.capacity()
	       % url.str());

    // Для тестового режима добавляем в информер HTML-комментарий со списком
    // кампаний и предложений, которые были доступны для данных параметров,
    // а также настройки подходящих кампаний, время обработки запроса и т.д.
    if (params.test_mode_) {
    long elapsed_usecs = (microsec_clock::local_time() - time_request_started_)
                         .total_microseconds();
	list<Campaign> campaigns;
	getCampaigns(params, campaigns);

	stringstream test_out;
	test_out <<
		"\n<!-- Подходящие кампании: \n";
	for (auto camp = campaigns.begin(); camp != campaigns.end(); camp++) {
	    test_out << "\n" << camp->title() << "\n";

	CampaignShowOptions *opt = CampaignOptionsCache::get(*camp);
	test_out << "Start show time: " << opt->start_show_time() << "\n";
	test_out << "End show time: " << opt->end_show_time() << "\n";

	    std::list<Offer> offers = Offers::x()->offers_by_campaign(*camp);
	    for (auto offer = offers.begin(); offer != offers.end(); offer++) {
		test_out << "    " << offer->title() << "\n";
	    }
	}
    test_out << "\nЗатраченное время: " << elapsed_usecs << " µs\n";
	test_out << "-->\n";
	informer_html.append(test_out.str());
    }

    return informer_html;
}


std::string Core::OffersToJson(const vector<ImpressionItem> &items) const
{
    LOG_IF(WARNING, items.empty()) << "No impressions items to show";
    std::stringstream json;
    json << "[";
    for (auto it = items.begin(); it != items.end(); it++) {
	if (it != items.begin())
	    json << ",";
	json << "{" <<
		"\"id\": \"" << EscapeJson(it->offer.id()) << "\"," <<
		"\"title\": \"" << EscapeJson(it->offer.title()) << "\"," <<
		"\"description\": \"" << EscapeJson(it->offer.description()) << "\"," <<
		"\"price\": \"" << EscapeJson(it->offer.price()) << "\"," <<
		"\"image\": \"" << EscapeJson(it->offer.image_url()) << "\"," <<
		"\"url\": \"" << EscapeJson(it->redirect_url) << "\"," <<
		"\"token\": \"" << EscapeJson(it->token) << "\"" <<
		"}";
    }

    json << "]";

    return json.str();
}


std::string Core::EscapeJson(const std::string &str)
{
    std::string result;
    for (auto it = str.begin(); it != str.end(); it++) {
	switch (*it) {
	case '\t':
	    result.append("\\t");
	    break;
	case '"':
	    result.append("\\\"");
	    break;
	case '\'':
	    result.append("\\'");
	    break;
	case '/':
	    result.append("\\/");
	    break;
	case '\b':
	    result.append("\\b");
	    break;
	case '\r':
	    result.append("\\r");
	    break;
	case '\n':
	    result.append("\\n");
	    break;
	default:
	    result.append(it, it + 1);
	    break;
	}
    }
    return result;
}


/** Возвращает отладочную информацию про текущий запрос */
std::string Core::RequestDebugInfo(const Core::Params &params) const
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
