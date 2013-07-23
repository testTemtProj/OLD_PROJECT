#ifndef CORE_H
#define CORE_H

#include <list>
#include <vector>
#include <map>
#include <utility>
#include <boost/date_time.hpp>
#include <boost/algorithm/string.hpp>
#include <amqpcpp.h>

#include "Rules.h"
#include "RandomEntity.h"
#include "Offer.h"
#include "Informer.h"


/// Класс, который связывает воедино все части системы.
class Core
{
public:

    /// Параметры, которые определяют показ рекламы.
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

	friend class Core;
	friend class GenerateToken;

    private:
	std::string ip_;
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
    };


    /** \brief  Единица показа.
     *
     *  Структура описывает одно место под рекламное предложение на информере.
     */
    struct ImpressionItem {
        ImpressionItem(const Offer &offer) : offer(offer) { }
        Offer offer;                ///< Рекламное предложение
        std::string token;          ///< Токен для проверки ссылки
        std::string redirect_url;   ///< Cсылка перенаправления
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


    /** \brief  Загружает все сущности, которые используются при показе
     *          рекламы. */
    void LoadAllEntities();
    
    /** \brief  Перезагружает кампанию \a campaign и всё относящееся к ней.
     *
     * \param campaign  Кампания, которая будет перезагружена.
     * */
    void ReloadCampaign(const Campaign &campaign);

    /** \brief  Обрабатывает новые сообщения в очереди RabbitMQ. */
    bool ProcessMQ();

    /** \brief  Возвращает список из \a count предложений для показа на
     *          заданных условиях.
     *
     *  \param count    Количество предложений, которые нужно показать.
     *  \param params   Условия показа.
     */
    std::vector<Offer> getOffers(int count, const Core::Params &params);

    /** \brief  Увеличивает счётчики показов предложений ``items`` */
    void markAsShown(const std::vector<ImpressionItem> &items,
		     const Core::Params &params);

    /** \brief  Выводит состояние службы и некоторую статистику */
    std::string Status();

    /** \brief  Возвращает HTML для информера, содержащего предложения items */
    std::string OffersToHtml(const std::vector<ImpressionItem> &items,
			     const Core::Params &params) const;

    /** \brief  Возвращает json-представление предложений ``items`` */
    std::string OffersToJson(const std::vector<ImpressionItem> &items) const;

    /** \brief  Возвращает безопасную json строку (экранирует недопустимые символы) */
    static std::string EscapeJson(const std::string &str);

    /** \brief  IP сервера, на котором запущена служба */
    std::string server_ip() const { return server_ip_; }
    void set_server_ip(const std::string &ip) {
	server_ip_ = ip;
    }

    /** \brief  Адрес скрипта перехода на рекламное предложение.
     *
     * По умолчанию равен \c "/redirect", то есть скрипт будет указывать
     * на тот же сервер, который отдал информер.
     *
     * Примеры значений:
     *
     * - \code http://rg.yottos.com/redirect \endcode
     * - \code http://getmyad.vsrv-1.2.yottos.com/redirect \endcode
     * - \code http://rynok.yottos.com/Redirect.ashx \endcode
    */
    std::string redirect_script() const { return redirect_script_; }
    void set_redirect_script(const std::string &url) {
	redirect_script_ = url;
    }

private:
    RandomEntity<Offer> &offers_by_campaign(const Campaign &campaign);
    void InitMessageQueue();
    void InitMongoDB();
    std::string RequestDebugInfo(const Core::Params &params) const;
    void LogToAmqp(const std::string &message);

    /** \brief  Возвращает в параметре \a out_campaigns список кампаний,
     *          подходящих под параметры \a params.
     */
    void getCampaigns(const Core::Params &params,
		      list<Campaign> &out_campaigns) const;

    /** \brief  Возвращает одно предложение, которое можно добавить к
     *          \a result
     */
    Offer _get_one_offer(const vector<Offer> &result,
                         RandomEntity<Campaign> &random_campaigns,
                         const vector<std::string> &excluded_offers);

    std::map<Campaign, RandomEntity<Offer> > offers_by_campaign_;

    bool amqp_initialized_;
    bool amqp_down_;
    AMQP *amqp_;
    AMQPExchange *exchange_;
    AMQPQueue *mq_campaign_; /// Очередь сообщений об изменениях в кампаниях
    AMQPQueue *mq_informer_; /// Очередь сообщений об изменениях в информерах
    AMQPQueue *mq_account_;  /// Очередь сообщений об изменениях в аккаунтах
    std::vector<std::string> mq_log_; /// История полученных сообщений MQ

    static int request_processed_; /// Счётчик обработанных запросов
    boost::posix_time::ptime time_service_started_; /// Время запуска службы
    boost::posix_time::ptime time_last_mq_check_;   /// Время последней проверки MQ
    boost::posix_time::ptime time_request_started_; /// Время начала последнего запроса

    std::string server_ip_;
    std::string redirect_script_;
};


#endif // CORE_H
