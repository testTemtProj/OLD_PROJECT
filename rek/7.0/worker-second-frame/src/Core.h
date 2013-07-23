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
#include "Params.h"


/// Класс, который связывает воедино все части системы.
class Core
{
public:

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
     * Core core(Params().ip("192.168.0.1")
     *                         .informer("informer#01"));
     * \endcode
     *
     * \param params    Параметры запроса.
     */
    std::string Process(const Params &params);


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

	/** \brief  Добавлено RealInvest Soft. Тот же метод getOffers(int count, const Params &params), но с заданием множества кампаний. Этот метод даёт возможность использовать "старую" ветку алгоритма, но список кампаний задавать извне.
     *
     *  \param count    Количество предложений, которые нужно показать.
     *  \param params   Условия показа.
     *  \param camps	Отобранные кампании.
     */
	std::vector<Offer> getOffers(int count, const Params &params, const list<Campaign>& camps);

	
	/** \brief  Новый алгоритм. Добавлен RealInvest Soft.
     *
     * Возвращает РП, отобранные для показа по новому алгоритму RISAlgorithm с учетом рейтингов РП внутри рекламных блоков
     * 
     * \param offersIds    Список пар (идентификатор, вес), где идентификатор - это идентификатор РП, отобранного поиском по индексу, вес - значение соответствия РП с данным идентификатором запросу (в алгоритме при вычислении веса вес, который вернула CLucene умножается на вес, задаваемый в настройках).
     * \param params    Параметры запроса.
     * \param camps    Список кампаний, по которым шёл выбор offersIds.
	 * \param offersRatingIds    Список значений рейтингов для РП внутри данного рекламного блока.
     * 
	 * \see RISAlgorithm
	 * \see createVectorOffersByIds
     */
	std::vector<Offer> getOffersRIS(const list<pair<pair<string, float>, pair<string, pair<string, string>>>> &offersIds, const Params &params, const list<Campaign> &camps, bool &clean, bool &updateShort, bool &updateContext);
	



    /** \brief  Увеличивает счётчики показов предложений ``items`` */
    void markAsShown(const std::vector<ImpressionItem> &items,
		     const Params &params, list<string> &shortTerm, list<string> &longTerm, list<string> &contextTerm);

    /** \brief  Выводит состояние службы и некоторую статистику */
    std::string Status();

    /** \brief  Возвращает HTML для информера, содержащего предложения items */
    std::string OffersToHtml(const std::vector<ImpressionItem> &items, map< string,float > &offersRatingIds,
			     const Params &params) const;

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
    std::string RequestDebugInfo(const Params &params) const;
    void LogToAmqp(const std::string &message);

    /** \brief  Возвращает в параметре \a out_campaigns список кампаний,
     *          подходящих под параметры \a params.
     */
    void getCampaigns(const Params &params,
		      list<Campaign> &out_campaigns) const;

    /** \brief  Возвращает в параметре \a out_campaigns список кампаний,
     *          подходящих под параметры \a params без учета привязки к РБ.
     */
    void getAllGeoCampaigns(const Params &params,
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
	
	/// Точка обмена
    AMQPExchange *exchange_;  
	/// Очередь сообщений об изменениях в кампаниях
    AMQPQueue *mq_campaign_; 
	
	/// Очередь сообщений об изменениях в информерах
    AMQPQueue *mq_informer_; 
	
	/// Очередь сообщений об изменениях в аккаунтах
    AMQPQueue *mq_account_;  
	
	/// История полученных сообщений MQ
    std::vector<std::string> mq_log_; 

	/// Счётчик обработанных запросов
    static int request_processed_; 

	static int offer_processed_;

	static int social_processed_;
	
	/// Время запуска службы
    boost::posix_time::ptime time_service_started_; 
	
	/// Время последней проверки MQ
    boost::posix_time::ptime time_last_mq_check_;   
	
	/// Время начала последнего запроса
    boost::posix_time::ptime time_request_started_; 

	///Адрес сервера
    std::string server_ip_;
	
	///Скрипт перенаправления запроса при клике на рекламном предложении
    std::string redirect_script_;


	/** \brief Создание вектора РП по списку их идентификаторов, полученного в результате обращения к индексу. */
	void createVectorOffersByIds(const list<pair<pair<string, float>, pair<string, pair<string, string>>>> &offersIds, vector<Offer> &result, const list<Campaign> &camps, const Params& params, bool &updateShort, bool &updateContext);
	



	/** \brief Удаление из вектора result баннеров, не подходящих по размеру для информера с идентификатором informer.
	 *
	 * @param result Вектор РП, которые нужно проверить на совместимость по размерам с инфомером informer.
	 * @param informer идентификатор информера, для которого модуль формирует ответ.
	 * 
	 * Добавлено RealInvest Soft.
	 */
	void filterOffersSize(vector<Offer> &result, const string& informerId);
	
	/** \brief Удаление из вектора result баннеров, не подходящих по размеру для информера informer.
	 *
	 * @param result Вектор РП, которые нужно проверить на совместимость по размерам с инфомером informer.
	 * @param informer Информер, для которого модуль формирует ответ.
	 * 
	 * Добавлено RealInvest Soft.
	 */
	void filterOffersSize(vector<Offer> &result, const Informer& informer);
	
	/** \brief Проверка принадлежности РП offer хотя бы одной кампании из списка camps.
	 ** 
	 * Добавлено RealInvest Soft.
	 * @param offer РП, которое нужно проверить.
	 * @param camps Список кампаний, на принадлежность к которым будет проверяться РП offer.
	 * @return true, если РП offer принадлежит хотя бы одной кампании из списка camps.
	 */
	bool isOfferInCampaigns(const Offer& offer, const list<Campaign>& camps);

	/** \brief Проверка размеров РП.
	  * 
	  * @param offer РП, которое нужно проверить по размеру.
	  * @param informer Информер, для которого модуль формирует ответ.
	  * 
	  * Добавлено RealInvest Soft. 
	  * 
	  * Если РП offer является баннером и его размеры не равны размерам РБ informer, возвращает false. Иначе - true. 
	  */
	bool checkBannerSize(const Offer& offer, const Informer& informer);
	
	/** \brief Основной алгоритм отбора РП RealInvest Soft. */
	void RISAlgorithm(vector<Offer> &result, const Params &params, bool &clean);

	/** \brief  Вычисление среднего рейтинга у РП типа typeOfferStr.
	 
	 \param vectorOffers Вектор РП, среди которых будет поиск тех, у которых нужно подсчитать средний рейтинг.
	 \param typeOfferStr Тип РП, среди которых нужно подсчитать средний рейтинг.
	 
	 Добавлено RealInvest Soft.
	 */
	float mediumRating(const vector<Offer>& vectorOffers, const string &typeOfferStr);
	bool isSocial (Offer& i);
};


#endif // CORE_H
