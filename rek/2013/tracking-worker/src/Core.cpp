#include "DB.h"
#include <boost/foreach.hpp>
#include <boost/date_time/posix_time/ptime.hpp>
#include <boost/date_time/posix_time/posix_time_io.hpp>
#include <boost/format.hpp>
#include <boost/algorithm/string.hpp>
#include <boost/algorithm/string/split.hpp>
#include <boost/regex.hpp>
#include <boost/regex/icu.hpp>
#include <glog/logging.h>
#include <ctime>
#include <cstdlib>
#include <sstream>
#include <mongo/util/version.h>
#include <mongo/bson/bsonobjbuilder.h>


#include "Core.h"
#include "InformerTemplate.h"
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

    InitMongoDB();
    time_service_started_ = second_clock::local_time();
}

Core::~Core()
{
}


/** Обработка запроса  с параметрами ``params``.
 **/
std::string Core::Process(const Params &params)
{
	boost::posix_time::ptime startTime, endTime;//добавлено для отладки, УДАЛИТЬ!!!

    request_processed_++;
    time_request_started_ = microsec_clock::local_time();

    try {
        markAsShown(params);
    } 
    catch (mongo::DBException &ex) {
	    LOG(ERROR) << "DBException during markAsShown(): " << ex.what();
    }

	return OffersToHtml();
}
/**
    \brief Нормализирует строку строку.

*/
std::string Core::stringWrapper(const string &str, bool replaceNumbers)
{
    try{
        boost::u32regex replaceSymbol = boost::make_u32regex("[^а-яА-Яa-zA-Z0-9-]");
        boost::u32regex replaceExtraSpace = boost::make_u32regex("\\s+");
        boost::u32regex replaceNumber = boost::make_u32regex("(\\b)\\d+(\\b)");
        string t = str;
        //Заменяю все не буквы, не цифры, не минус на пробел
        t = boost::u32regex_replace(t,replaceSymbol," ");
        if (replaceNumbers)
        {
            //Заменяю отдельностояшие цифры на пробел, тоесть "у 32 п" замениться на
            //"у    п", а "АТ-23" останеться как "АТ-23"
            t = boost::u32regex_replace(t,replaceNumber," ");
        }
        //Заменяю дублируюшие пробелы на один пробел
        t = boost::u32regex_replace(t,replaceExtraSpace," ");
        boost::trim(t);
        return t;
    }
    catch (std::exception const &ex)
    {
        LOG(ERROR) << "exception " << typeid(ex).name() << ": " << ex.what();
        LOG(ERROR) << "exception query" << str;
        return string();
    }
}


/** Подготовка базы данных MongoDB.
*/
void Core::InitMongoDB()
{
    mongo::DB db("log");
    const int K = 1000;
    const int M = 1000 * K;
    db.createCollection("log.tracking", 600*M, true, 1*M);
}


/** Добавляет в журнал просмотров log.impressions предложения \a items.
    Если показ информера осуществляется в тестовом режиме, запись не происходит.

    Внимание: Используется база данных, зарегистрированная под именем 'log'.
 */
void Core::markAsShown(const Params &params)
{
    mongo::DB db("log");
	std::tm dt_tm;
	dt_tm = boost::posix_time::to_tm(params.time_);
	mongo::Date_t dt( (mktime(&dt_tm)) * 1000LLU);
					
	mongo::BSONObj record = mongo::BSONObjBuilder().genOID().
								append("dt", dt).
								append("ip", params.ip_).
								append("cookie", params.cookie_id_).
								append("cookie_tracking", params.cookie_tracking_).
								append("remarketing_url", params.location_).
								append("account_id", params.account_id_).
								append("search", stringWrapper(params.search_, true)).
								append("context", stringWrapper(params.context_, true)).
								obj();

	db.insert("log.tracking", record, true);
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
    out <<  "<tr><td>Сборка: </td><td>" << __DATE__ << " " << __TIME__ <<
	    "</td></tr>";
    out <<  "<tr><td>Драйвер mongo: </td><td>" << mongo::versionString <<
	    "</td></tr>";
    out << "</table>\n";
    out << "</body>\n</html>\n";

    return out.str();
}

std::string Core::OffersToHtml() const 
{
    std::string informer_html;
    informer_html =	InformerTemplate::instance()->getTemplate();
    return informer_html;
}
