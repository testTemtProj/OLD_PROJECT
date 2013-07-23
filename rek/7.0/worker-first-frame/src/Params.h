#ifndef PARAMS_H
#define PARAMS_H

#include <boost/date_time.hpp>
#include <string>


/** \brief Параметры, которые определяют показ рекламы */
class Params
{
public:
	/// IP посетителя.
	Params &ip(const std::string &ip) {
	    ip_ = ip;
	    return *this;
	}

	Params &cookie_name(const std::string &cookie_name) {
	    cookie_name_ = cookie_name;
	    return *this;
	}

	Params &cookie_domain(const std::string &cookie_domain) {
	    cookie_domain_ = cookie_domain;
	    return *this;
	}
    ///
	Params &query(const std::string &query) {
	    query_ = query;
	    return *this;
	}
	/// ID информера.
	Params &informer(const std::string &informer) {
	    informer_ = informer;
	    boost::to_lower(informer_);
	    return *this;
	}
	/// Время. По умолчанию равно текущему моменту.
	Params &time(const boost::posix_time::ptime &time) {
	    time_ = time;
	    return *this;
	}



	/** \brief  Виртуальный путь и имя вызываемого скрипта.

	    Используется для построения ссылок на самого себя. Фактически,
	    сюда должна передаваться сервреная переменная SCRIPT_NAME.
    */
	Params &script_name(const char *script_name) {
	    script_name_ = script_name? script_name : "";
	    return *this;
	}


	Params &w(const std::string &w) {
	   w_ = w;
	   return *this;
	}

	Params &h(const std::string &h) {
	   h_ = h;
	   return *this;
	}


	std::string getIP() const {return ip_;}
    std::string getCookieName() const {return cookie_name_;}
    std::string getCookieDomain() const {return cookie_domain_;}
    std::string getQuery() const {return query_;}
	std::string getInformer() const {return informer_;}
	boost::posix_time::ptime getTime() const {return time_;}
	std::string getScriptName() const {return script_name_;}
	std::string getW() const {return w_;}
	std::string getH() const {return h_;}

	friend class Core;

private:
	std::string ip_;
    std::string cookie_name_;
    std::string cookie_domain_;
    std::string query_;
	std::string informer_;
	boost::posix_time::ptime time_;
	std::string script_name_;
	std::string w_;
	std::string h_;
};

#endif // PARAMS_H
