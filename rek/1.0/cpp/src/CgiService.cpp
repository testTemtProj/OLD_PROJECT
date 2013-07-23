#include "DB.h"
#include <glog/logging.h>
#include <boost/algorithm/string.hpp>

#include "CgiService.h"
#include "utils/UrlParser.h"
#include "utils/GeoIPTools.h"
#include "Core.h"
#include "Informer.h"
#include <fcgi_stdio.h>

using namespace std;


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
    if (!ConnectDatabase()) {
	// Возвращаем 503 на все запросы до тех пор, пока не подключимся
	while (FCGI_Accept() >= 0 && !ConnectDatabase())
	    Response("Error connecting to database", 503);
	Response("", 200);
    }

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
		       getenv("SCRIPT_NAME", ""));
    }
}


void CgiService::ProcessRequest(const std::string &query,
				const std::string &ip,
				const std::string script_name)
{
	UrlParser url(query);

	if (url.param("show") == "status") {
	Response(core->Status(), 200);
	    return;
	}

    using namespace boost::algorithm;
	std::vector<std::string> excluded_offers;
	std::string exclude = url.param("exclude");
	boost::split(excluded_offers, exclude, boost::is_any_of("_"));

	try {
	    string result = core->Process(Core::Params()
					 .ip(ip)
					 .informer(url.param("scr"))
					 .country(url.param("country"))
					 .region(url.param("region"))
					 .test_mode(url.param("test") == "true")
					 .json(url.param("show") == "json")
					 .excluded_offers(excluded_offers)
					 .script_name(script_name.c_str())
					 .location(url.param("location"))
					 .referrer(url.param("referrer"))
					 );

	Response(result, 200);

	} catch (std::exception const &ex) {
	Response("", 503);
	    LOG(ERROR) << "exception " << typeid(ex).name() << ": " << ex.what()
		       << " while processing " << query;
	}
}

