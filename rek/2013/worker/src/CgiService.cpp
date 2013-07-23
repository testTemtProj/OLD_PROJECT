#include "DB.h"
#include <glog/logging.h>
#include <boost/algorithm/string.hpp>

#include "CgiService.h"
#include "utils/UrlParser.h"
#include "utils/GeoIPTools.h"
#include "Core.h"
#include "Informer.h"
#include "utils/SearchEngines.h"
#include "HistoryManager.h"
#include "InformerTemplate.h"
#include <fcgi_stdio.h>
#include "utils/Cookie.h"

using namespace std;
using namespace ClearSilver;
using namespace boost;

std::string time_t_to_string(time_t t);

    string
convert (const posix_time::ptime& t)
{
    ostringstream ss;
    ss.exceptions(ios_base::failbit);

    date_time::time_facet<posix_time::ptime, char>* facet
        = new date_time::time_facet<posix_time::ptime, char>;
    ss.imbue(locale(locale::classic(), facet));

    facet->format("%a, %d-%b-%Y %T GMT");
    ss.str("");
    ss << t;
    return ss.str();
}

CgiService::CgiService(int argc, char *argv[])
    : argc(argc), argv(argv), core(0)
{
    mongo_main_host_ = getenv("mongo_main_host", "localhost");
    mongo_main_db_ = getenv("mongo_main_db", "getmyad_db");
    mongo_main_set_ = getenv("mongo_main_set", "");
    mongo_main_slave_ok_ = (getenv("mongo_main_slave_ok", "false") == "true");

    mongo_log_host_ = getenv("mongo_log_host", "localhost");
    mongo_log_db_ = getenv("mongo_log_db", "getmyad");
    mongo_log_set_ = getenv("mongo_log_set", "");
    mongo_log_slave_ok_ = (getenv("mongo_log_slave_ok", "false") == "true");

    if (getenv("SERVER_ADDR"))
	    server_ip_ = getenv("SERVER_ADDR");
    else
    	LOG(ERROR) << "SERVER_ADDR not set! Redirect links may be invalid!";

    if (getenv("REDIRECT_SCRIPT_URL"))
    	redirect_script_ = getenv("REDIRECT_SCRIPT_URL");

    if (!GeoCity(getenv("GEOIP_CITY_PATH")))
	LOG(ERROR) << "City database not found! City targeting will be disabled.";

	redis_short_term_history_host_ = getenv("redis_short_term_history_host", "127.0.0.1");
	redis_short_term_history_port_ = getenv("redis_short_term_history_port", "6380");
	redis_long_term_history_host_ = getenv("redis_long_term_history_host", "127.0.0.1");
	redis_long_term_history_port_ = getenv("redis_long_term_history_port", "6382");
	redis_user_view_history_host_ = getenv("redis_user_view_history_host", "127.0.0.1");
	redis_user_view_history_port_ = getenv("redis_user_view_history_port", "6381");
	redis_page_keywords_host_ = getenv("redis_page_keywords_host", "127.0.0.1");
	redis_page_keywords_port_ = getenv("redis_page_keywords_port", "6383");
	redis_category_host_ = getenv("redis_category_host", "127.0.0.1");
	redis_category_port_ = getenv("redis_category_port", "6384");
	redis_retargeting_host_ = getenv("redis_retargeting_host", "127.0.0.1");
	redis_retargeting_port_ = getenv("redis_retargeting_port", "6385");

	range_query_ = atof(getenv("range_query", "1").c_str());
	range_short_term_ = atof(getenv("range_short_term", "0.75").c_str());
	range_long_term_ = atof(getenv("range_long_term", "0.5").c_str());
	range_context_ = atof(getenv("range_context", "0.8").c_str());
	range_context_term_ = atof(getenv("range_context_term", "0.70").c_str());
	range_on_places_ = atof(getenv("range_on_places", "0.1").c_str());

	shortterm_expire_= getenv("shortterm_expire", "864000") ;//24 hours default
	views_expire_ = getenv("views_expire", "864000") ;//24 hours default
	context_expire_ = getenv("context_expire", "864000") ;//24 hours default

	folder_offer_ = getenv("index_folder_offer", "/var/www/indexOffer");
	folder_informer_ = getenv("index_folder_informer", "/var/www/indexInformer");
}

CgiService::~CgiService()
{
    delete core;
}


string CgiService::getenv(const char *name, const char *default_value)
{
    char *value = getenv(name);
    return value? value : default_value;
}


void CgiService::Response(const char *out, int status,
			  const char *content_type, const Cookie cookie)
{
    string headers;
    headers += "Content-type: ";
    headers += content_type;
    headers += "\r\n";


    headers += "Set-Cookie: ";
    headers += cookie.to_string();
    headers += "\r\n";

    headers += "Status: ";
    switch (status) {
	case 200:
	    headers += "200 OK";
	    break;
	case 301:
	    headers += "301 Moved Permanently";
	    break;
	case 302:
	    headers += "302 Found";
	    break;
	case 307:
	    headers += "307 Temporary Redirect";
	    break;
	case 400:
	    headers += "400 Bad Request";
	    break;
	case 403:
	    headers += "403 Forbidden";
	    break;
	case 500:
	    headers += "500 Internal Server Error";
	    break;
	case 503:
	    headers += "503 Service Unavailable";
	    break;
	default:
	    headers += "200 OK";
	    LOG(WARNING) << "Attempt to return unknown HTTP status: " <<
			    status;
	    break;
    }
    headers += "\r\n";

    puts(headers.c_str());
    puts(out);
}


void CgiService::Response(const std::string &out, int status,
			  const char *content_type, const Cookie cookie)
{
    Response(out.c_str(), status, content_type, cookie);
}

bool CgiService::ConnectDatabase()
{
    LOG(INFO) << "Connecting to " << mongo_main_host_ << "/" << mongo_main_db_;

    try {
    	if (mongo_main_set_.empty())
    	    mongo::DB::addDatabase(
		    mongo_main_host_,
		    mongo_main_db_,
		    mongo_main_slave_ok_);
    	else
    	    mongo::DB::addDatabase(
		    mongo::DB::ReplicaSetConnection(
			    mongo_main_set_,
			    mongo_main_host_),
		    mongo_main_db_,
		    mongo_main_slave_ok_);

    	if (mongo_log_set_.empty())
    	    mongo::DB::addDatabase( "log",
			    mongo_log_host_,
			    mongo_log_db_,
			    mongo_log_slave_ok_);
    	else
    	    mongo::DB::addDatabase( "log",
		    mongo::DB::ReplicaSetConnection(
			    mongo_log_set_,
			    mongo_log_host_),
			    mongo_log_db_,
			    mongo_log_slave_ok_);

	// Проверяем доступность базы данных
    	mongo::DB db;
    	mongo::DB db_log("log");
	db.findOne("domain.categories", mongo::Query());

    } catch (mongo::UserException &ex) {
    	LOG(ERROR) << "Error connecting to mongo:";
    	LOG(ERROR) << ex.what();
    	return false;
    }

    return true;
}


void CgiService::Serve()
{

	RISinit();

	core = new Core();
    core->set_server_ip(server_ip_);
    core->set_redirect_script(redirect_script_);

    while (FCGI_Accept() >= 0) {

	string query = getenv("QUERY_STRING",
			      (argc > 1)? argv[1] : "");
    if (query.empty() && !getenv("QUERY_STRING")) {
	    puts("Используйте getmyad-worker или как fastcgi модуль, "
		 "или из командой строки: \n"
		 "getmyad-worker QUERY_STRING \n");
	    return;
	    }

	ProcessRequest(query,
		       getenv("REMOTE_ADDR", ""),
		       getenv("SCRIPT_NAME", ""),
               getenv("HTTP_COOKIE", ""));
    }

}


void CgiService::ProcessRequest(const std::string &query,
				const std::string &ip,
				const std::string script_name,
                const std::string visitor_cookie)
{
    //uint64_t strr = Misc::currentTimeMillis();
    LOG(INFO) << query;
	UrlParser url(query);

	if (url.param("show") == "status") {
	Response(core->Status(), 200);
	    return;
	}

    using namespace boost::algorithm;
	std::vector<std::string> excluded_offers;
	std::string exclude = url.param("exclude");
	boost::split(excluded_offers, exclude, boost::is_any_of("_"));


    string cookie_name = getenv("cookie_parameter_name", "yottos_unique_id");
    string cookie_value = time_t_to_string(time(NULL));


    std::vector<std::string> strs;
    boost::split(strs, visitor_cookie, boost::is_any_of(";"));

    for (unsigned int i=0; i<strs.size(); i++){
        if(strs[i].find(cookie_name) != string::npos){
            std::vector<std::string> name_value;
            boost::split(name_value, strs[i], boost::is_any_of("="));
            if (name_value.size() == 2)
                cookie_value = name_value[1];
        }
    }


    Cookie::Expires expires = Cookie::Expires(posix_time::second_clock::local_time() + years(1));
    Cookie::Path path = Cookie::Path(getenv("cookie_path", "/"));
    Cookie::Authority authority = Cookie::Authority(getenv("cookie_domain",".yottos.com"));

    Cookie c = Cookie(cookie_name, 
                           cookie_value, 
                           Cookie::Credentials(authority, 
                                               path, 
                                               expires));
	try {
	    string result = core->Process(Params()
					 .ip(ip)
                     .cookie_id(cookie_value)
					 .informer(url.param("scr"))
					 .country(url.param("country"))
					 .region(url.param("region"))
					 .test_mode(url.param("test") == "true")
					 .json(url.param("show") == "json")
					 .excluded_offers(excluded_offers)
					 .script_name(script_name.c_str())
					 .location(url.param("location"))
					 .w(url.param("w"))
					 .h(url.param("h"))
                     .search(url.param("search"))
                     .context(url.param("context"))
					 );
    //LOG(INFO) << "Формирование Рекламы " << (int32_t)(Misc::currentTimeMillis() - strr) << " мс";

        Response(result, 200, "text/html", c);

	} catch (std::exception const &ex) {
	Response("", 503);
	    LOG(ERROR) << "exception " << typeid(ex).name() << ": " << ex.what()
		       << " while processing " << query;
	}
}

/** Все необходимые действия для инициализации модуля вынесены в отдельный метод. */
void CgiService::RISinit()
{

	//подключаемся к mongo. операция критическая и без неё модуль не сможет работать.
	if (!ConnectDatabase()) {
		// Возвращаем 503 на все запросы до тех пор, пока не подключимся
		while (FCGI_Accept() >= 0 && !ConnectDatabase())
			Response("Error connecting to database", 503);
		Response("", 200);
	}

	/* инициализируем структуру соответствий поисковиков значениям параметров.
	 * это необходимо для разбора строки запроса с поисковика.
	 * если структура не проинициализирована, то модуль будет работать, но строка разбираться не будет.
	 * операция не критическая (модуль не упадёт), но желательная, т.к. это функциональность нового модуля.*/
	//инициализация структуры, хранящей соответствия названий поисковиков зничениям параметров
	if(!SearchEngineMapContainer::instance()->setSearchEnginesMap("SearchEngines.txt"))
	{
		LOG(WARNING) << "Хранилище соответствий поисковиков значениям параметров не проинициализировано. Строка запроса с поисковика, которую вбил пользователь, разбираться не будет.\n";
	}
	else
	{
		LOG(INFO) << "Хранилище соответствий поисковиков значениям параметров проинициализировано.\n";
	}

	

	////инициализация HistoryManager (redis + lucene)
	DBConnectionParams param (
	redis_short_term_history_host_,
	redis_short_term_history_port_,
	redis_long_term_history_host_,
	redis_long_term_history_port_,
	redis_user_view_history_host_,
	redis_user_view_history_port_,
	redis_page_keywords_host_,
	redis_page_keywords_port_,
	redis_category_host_,
	redis_category_port_,
	redis_retargeting_host_,
	redis_retargeting_port_,
	shortterm_expire_,
	context_expire_,
	views_expire_);



	//подключаемся к redis. операция критическая и без неё модуль не сможет работать.
	if (HistoryManager::instance()->initDB(param)==-1) {
		// Возвращаем 503 на все запросы до тех пор, пока не подключимся
		while (FCGI_Accept() >= 0 && HistoryManager::instance()->initDB(param)==-1)
			Response("Error connecting to database", 503);
		Response("", 200);
	}

	//инициализируем шаблоны. операция критическая, т.к. без неё модуль не сможет отображать баннеры в принципе.
	if (!InformerTemplate::instance()->init())
	{
		LOG(ERROR) << "Сбой при инициализации шаблонов.";
		while (FCGI_Accept() >= 0 && InformerTemplate::instance()->init()==false)
		{
			Response("Error templates' initialization", 503);
		}
		Response("", 200);
	}
	else{
		LOG(INFO) << "Шаблоны проинициализированы.";
	}

	//задаём параметры для весов (для шести запросов к индексу lucene)
	HistoryManager::instance()->initWeights(
		100.0,
		range_query_,
		range_short_term_,
		range_long_term_,
		range_context_,
		range_context_term_,
		range_on_places_
		);

	HistoryManager::instance()->initLuceneIndexParams(folder_offer_, folder_informer_);

	LOG(INFO) << "HistoryManager проинициализирован.";
}

std::string time_t_to_string(time_t t)
{
        std::stringstream sstr;
            sstr << t;
                return sstr.str();
}
