#ifndef PARAMS_H
#define PARAMS_H

#include <boost/date_time.hpp>
#include <string>


/** \brief Параметры, которые определяют показ рекламы */
class Params
{
public:
	Params() : test_mode_(false), json_(false) {
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

	/** \brief  Двухбуквенный код страны посетителя.
      
	    Если не задан, то страна будет определена по IP.

	    Этот параметр используется служебными проверками работы информеров
	    в разных странах и в обычной работе не должен устанавливаться.

        \see region()
        \see ip()
    */
	Params &country(const std::string &country) {
	    country_ = country;
	    return *this;
	}

	/** \brief  Гео-политическая область в написании MaxMind GeoCity.

	    Если не задана, то при необходимости будет определена по IP.

	    Вместе с параметром country() используется служебными проверками
	    работы информеров в разных странах и в обычной работе не должен
	    устанавливаться.
        
        \see country()
        \see ip()
    */
	Params &region(const std::string &region) {
	    region_ = region;
	    return *this;
	}

	/** \brief  Тестовый режим работы, в котором показы не записываются.

	    По умолчанию равен false.
    */
	Params &test_mode(bool test_mode) {
	    test_mode_ = test_mode;
	    return *this;
	}

	/// Выводить ли предложения в формате json.
	Params &json(bool json) {
	    json_ = json;
	    return *this;
	}

	/// ID предложений, которые следует исключить из показа.
	Params &excluded_offers(const std::vector<std::string> &excluded) {
	    excluded_offers_ = excluded;
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

	/** \brief  Адрес страницы, с которой посетитель попал на сайт-партнёр с
	    установленной выгрузкой.
        
        Обычно передаётся из javascript загрузчика.
    */
	Params &referrer(const char *referrer) {
	    return this->referrer(referrer? referrer : "");
	}

	/** \brief  Адрес страницы, с которой посетитель попал на сайт-партнёр с
	    установленной выгрузкой.
        
        Обычно передаётся из javascript загрузчика.
    */
	Params &referrer(const std::string referrer) {
	    referrer_ = referrer;
	    return *this;
	}

	/** \brief  Адрес страницы, на которой показывается информер.
        
	    Обычно передаётся javascript загрузчиком.
    */
	Params &location(const char *location) {
	    return this->location(location? location : "");
	}

	/** \brief  Адрес страницы, на которой показывается информер.
        
	    Обычно передаётся javascript загрузчиком.
    */
	Params &location(const std::string &location) {
	   location_ = location;
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

	/**
	 * добавлено RealInvest Soft
	 * строка, которую пользователь вбил в поисковике, если пользователь перешёл с поисковика.
	 */
	Params& userQueryString(const std::string &userQueryString)
	{
		userQueryString_ = userQueryString;
		return *this;
	}
	Params& userQueryString(const char *userQueryString) {
		return this->userQueryString(userQueryString? userQueryString : "");
	}

	/**
	 * строка, содержашяя контекст страницы
	 */
	Params& context(const std::string &context)
	{
		context_ = context;
		return *this;
	}
	Params& context(const char *context) {
		return this->context(context? context : "");
	}

	std::string getIP() const {return ip_;}
    std::string getCookieId() const {return cookie_id_;}
    std::string getUserKey() const {return cookie_id_;}
	std::string getCountry() const {return country_;}
	std::string getRegion() const {return region_;}
	std::string getInformer() const {return informer_;}
	boost::posix_time::ptime getTime() const {return time_;}
	bool isTestMode() const {return test_mode_;}
	bool isJson() const {return json_;}
	std::vector<std::string> getExcludedOffers() {return excluded_offers_;}
	std::string getScriptName() const {return script_name_;}
	std::string getReferrer() const {return referrer_;}
	std::string getLocation() const {return location_;}
	std::string getW() const {return w_;}
	std::string getH() const {return h_;}
	std::string getUserQueryString() const {return userQueryString_;}
	std::string getContext() const {return context_;}

	friend class Core;
	friend class GenerateToken;
	friend class HistoryManager;//добавлено RealInvest Soft

private:
	std::string ip_;
    std::string cookie_id_;
	std::string country_;
	std::string region_;
	std::string informer_;
	boost::posix_time::ptime time_;
	bool test_mode_;
	bool json_;
	std::vector<std::string> excluded_offers_;
	std::string script_name_;
	std::string referrer_;
	std::string location_;
	std::string w_;
	std::string h_;

	//добавлено RealInvest Soft
	std::string userQueryString_;//строка, которую пользователь вбил в поисковике, если пользователь перешёл с поисковика.
	std::string context_;//строка содержашяя контекст страницы


};

#endif // PARAMS_H
