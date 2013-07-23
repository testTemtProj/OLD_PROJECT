#ifndef PARAMS_H
#define PARAMS_H

#include <boost/date_time.hpp>
#include <string>


/** \brief Параметры, которые определяют показ рекламы */
class Params
{
public:
	Params(){
	    time_ = boost::posix_time::second_clock::local_time();
	}

	/// IP посетителя.
	Params &ip(const std::string &ip) {
	    ip_ = ip;
	    return *this;
	}

    /// ID посетителя, взятый из cookie
	Params &cookie_id(const std::string &cookie_id) {
	    cookie_id_ = cookie_id;
	    return *this;
	}
    /// ID трекинга посетителя, взятый из cookie
	Params &cookie_tracking(const std::string &cookie_tracking) {
	    cookie_tracking_ = cookie_tracking;
	    return *this;
	}
	/// Время. По умолчанию равно текущему моменту.
	Params &time(const boost::posix_time::ptime &time) {
	    time_ = time;
	    return *this;
	}

	/** \brief  Адрес страницы, на которой показывается информер.
        
	    Обычно передаётся javascript загрузчиком.
    */
	Params &location(const std::string &location) {
	   location_ = location;
	   return *this;
	}

	Params &account_id(const std::string &account_id) {
	   account_id_ = account_id;
	   return *this;
	}

	/**
	 * строка, содержашяя контекст страницы
	 */
	Params &context(const std::string &context)
	{
		context_ = context;
		return *this;
	}
	Params &context(const char *context) {
		return this->context(context? context : "");
	}
	/**
	 * строка, содержашяя поисковый запрос
	 */
	Params &search(const std::string &search)
	{
		search_ = search;
		return *this;
	}
	Params &search(const char *search) {
		return this->search(search? search : "");
	}

	std::string getIP() const {return ip_;}
    std::string getCookieId() const {return cookie_id_;}
    std::string getCookieTracking() const {return cookie_tracking_;}
    std::string getUserKey() const {return cookie_id_ + "-" + ip_;}
	boost::posix_time::ptime getTime() const {return time_;}
	std::string getLocation() const {return location_;}
	std::string getAccountId() const {return account_id_;}
	std::string getContext() const {return context_;}
	std::string getSearch() const {return search_;}

	friend class Core;

private:
	std::string ip_;
    std::string cookie_id_;
    std::string cookie_tracking_;
	boost::posix_time::ptime time_;
	std::string location_;
	std::string account_id_;
	std::string context_;//строка содержашяя контекст страницы
    std::string search_;

};

#endif // PARAMS_H
