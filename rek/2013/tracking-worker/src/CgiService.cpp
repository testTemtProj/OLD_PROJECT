#include "DB.h"
#include <glog/logging.h>
#include <boost/algorithm/string.hpp>
#include <boost/lexical_cast.hpp>

#include "CgiService.h"
#include "utils/UrlParser.h"
#include "Core.h"
#include "InformerTemplate.h"
#include <fcgi_stdio.h>
#include "utils/Cookie.h"

using namespace std;
using namespace ClearSilver;
using namespace boost;

std::string time_t_to_string(time_t t);

string convert(const posix_time::ptime& t)
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
    mongo_log_db_ = getenv("mongo_log_db", "getmyad_tracking");
    mongo_log_set_ = getenv("mongo_log_set", "");
    mongo_log_slave_ok_ = (getenv("mongo_log_slave_ok", "false") == "true");
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
			  const char *content_type, const Cookie cookie_id, const Cookie cookie_track)
{
    string headers;
    headers += "Content-type: ";
    headers += content_type;
    headers += "\r\n";


    headers += "Set-Cookie: ";
    headers += cookie_id.to_string();
    headers += "\r\n";
    headers += "Set-Cookie: ";
    headers += cookie_track.to_string();
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
			  const char *content_type, const Cookie cookie_id, const Cookie cookie_track)
{
    Response(out.c_str(), status, content_type, cookie_id, cookie_track);
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

    string cookie_unique_id_name = getenv("cookie_unique_id_parameter_name", "yottos_unique_id");
    string cookie_tracking_name = getenv("cookie_tracking_parameter_name", "yottos_tracking_id");
    string cookie_value_unique_id = time_t_to_string(time(NULL));
    string cookie_value_tracking = time_t_to_string(time(NULL));


    std::vector<std::string> strs;
    boost::split(strs, visitor_cookie, boost::is_any_of(";"));

    for (unsigned int i=0; i<strs.size(); i++){
        if(strs[i].find(cookie_unique_id_name) != string::npos){
            std::vector<std::string> name_value_unique_id;
            boost::split(name_value_unique_id, strs[i], boost::is_any_of("="));
            if (name_value_unique_id.size() == 2)
                cookie_value_unique_id = name_value_unique_id[1];
        }
        if(strs[i].find(cookie_tracking_name) != string::npos){
            std::vector<std::string> name_value_tracking;
            boost::split(name_value_tracking, strs[i], boost::is_any_of("="));
            if (name_value_tracking.size() == 2)
                cookie_value_tracking = name_value_tracking[1];
        }
    }
    if (cookie_value_tracking != cookie_value_unique_id)
    {
        cookie_value_tracking = cookie_value_unique_id;
    }


    Cookie::Expires expires_unique_id = Cookie::Expires(posix_time::second_clock::local_time() + boost::gregorian::years(1));
    Cookie::Expires expires_tracking;
    try
    {
        expires_tracking = Cookie::Expires(posix_time::second_clock::local_time() + boost::gregorian::days(lexical_cast<int>(url.param("time"))));
    }
    catch (bad_lexical_cast &)
    {
        expires_tracking = Cookie::Expires(posix_time::second_clock::local_time() + boost::gregorian::years(1));
    }
    Cookie::Path path_unique_id = Cookie::Path(getenv("cookie_unique_id_path", "/"));
    Cookie::Path path_tracking = Cookie::Path(getenv("cookie_tracking_path", "/"));
    Cookie::Authority authority_unique_id = Cookie::Authority(getenv("cookie_unique_id_domain",".yottos.com"));
    Cookie::Authority authority_tracking = Cookie::Authority(getenv("cookie_tracking_domain",".yottos.com"));

    Cookie c_id = Cookie(cookie_unique_id_name, 
                           cookie_value_unique_id, 
                           Cookie::Credentials(authority_unique_id, 
                                               path_unique_id, 
                                               expires_unique_id));
    Cookie c_track = Cookie(cookie_tracking_name, 
                           cookie_value_tracking, 
                           Cookie::Credentials(authority_tracking, 
                                               path_tracking, 
                                               expires_tracking));
	try {
	    string result = core->Process(Params()
					 .ip(ip)
                     .cookie_id(cookie_value_unique_id)
                     .cookie_tracking(cookie_value_tracking)
					 .location(url.param("location"))
                     .account_id(url.param("ac"))
                     .search(url.param("search"))
                     .context(url.param("context"))
					 );

        Response(result, 200, "text/html", c_id, c_track);

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
}

std::string time_t_to_string(time_t t)
{
        std::stringstream sstr;
            sstr << t;
                return sstr.str();
}
