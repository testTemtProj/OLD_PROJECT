#include "DB.h"
#include <glog/logging.h>
#include <boost/algorithm/string.hpp>

#include "CgiService.h"
#include "utils/UrlParser.h"
#include "Core.h"
#include "Informer.h"
#include "FrameTemplate.h"
#include <fcgi_stdio.h>

using namespace std;
using namespace boost;

CgiService::CgiService(int argc, char *argv[])
    : argc(argc), argv(argv), core(0)
{
    mongo_main_host_ = getenv("mongo_main_host", "localhost");
    mongo_main_db_ = getenv("mongo_main_db", "getmyad_db");
    mongo_main_set_ = getenv("mongo_main_set", "");
    mongo_main_slave_ok_ = (getenv("mongo_main_slave_ok", "false") == "true");


    if (getenv("SERVER_ADDR"))
	    server_ip_ = getenv("SERVER_ADDR");
    else
    	LOG(ERROR) << "SERVER_ADDR not set! Redirect links may be invalid!";

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
			  const char *content_type)
{
    string headers;
    headers += "Content-type: ";
    headers += content_type;
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
			  const char *content_type)
{
    Response(out.c_str(), status, content_type);
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

    mongo::DB db;
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


void CgiService::ProcessRequest(const std::string &query, const std::string &ip, const std::string script_name, const std::string visitor_cookie)
{
	UrlParser url(query);

	if (url.param("show") == "status") {
	Response(core->Status(), 200);
	    return;
	}
    using namespace boost::algorithm;


    string cookie_name = getenv("cookie_parameter_name", "yottos_unique_id");
    string cookie_domain = getenv("cookie_domain", ".yottos.com");


	try {
	    string result = core->Process(Params()
					 .ip(ip)
                     .cookie_name(cookie_name)
                     .cookie_domain(cookie_domain)
					 .informer(url.param("scr"))
					 .script_name(script_name.c_str())
					 .w(url.param("w"))
					 .h(url.param("h"))
                     .query(query)
					 );
        Response(result, 200, "text/html");

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
	if (!FrameTemplate::instance()->init())
	{
		LOG(ERROR) << "Сбой при инициализации шаблонов.";
		while (FCGI_Accept() >= 0 && FrameTemplate::instance()->init()==false)
		{
			Response("Error templates' initialization", 503);
		}
		Response("", 200);
	}
	else{
		LOG(INFO) << "Шаблоны проинициализированы.";
	}

}
