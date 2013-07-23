#ifndef CORE_H
#define CORE_H

#include <list>
#include <vector>
#include <map>
#include <utility>
#include <boost/date_time.hpp>
#include <boost/algorithm/string.hpp>

/// Класс, который связывает воедино все части системы.
class Core
{
public:

    /// Параметры, которые определяют показ рекламы.
    class Params
    {
    public:
	Params() {
	    time_ = boost::posix_time::second_clock::local_time();
	}

	/// IP посетителя.
	Params &ip(const std::string &ip) {
	    ip_ = ip;
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

    Params &rawQuery(const std::string &rawQuery){
        rawQuery_ = rawQuery;
        return *this;
    }

	friend class Core;

    private:
	std::string ip_;
	std::string informer_;
	boost::posix_time::ptime time_;
	std::string referrer_;
	std::string location_;
    std::string rawQuery_;
    };

    /** \brief  Создаёт ядро.
     *
     * Производит все необходимые инициализации:
     *
     * - Загружает все сущности из базы данных;
     * - Подключается к RabbitMQ и создаёт очереди сообщений;
     * - При необходимости создаёт локальную базу данных MongoDB с нужными
     *   параметрами.
     */
    Core();

    /** Пытается красиво закрыть очереди RabbitMQ, но при работе с FastCGI
     *  никогда не вызывается (как правило, процессы просто снимаются).
     */
    ~Core();

    /** \brief  Обработка запроса на показ рекламы.
     *
     * Самый главный метод. Возвращает HTML-строку, которую нужно вернуть
     * пользователю.
     *
     * Пример вызова:
     *
     * \Example
     * \code
     * Core core(Core::Params().ip("192.168.0.1")
     *                         .informer("informer#01"));
     * \endcode
     *
     * \param params    Параметры запроса.
     */
    std::string Process(const Core::Params &params);

    /** \brief  IP сервера, на котором запущена служба */
    std::string server_ip() const { return server_ip_; }
    void set_server_ip(const std::string &ip) {
	server_ip_ = ip;
    }

private:
    void InitMongoDB();
    std::string server_ip_;
};


#endif // CORE_H
