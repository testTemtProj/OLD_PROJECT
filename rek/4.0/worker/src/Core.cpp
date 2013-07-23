#include "DB.h"
#include <boost/foreach.hpp>
#include <boost/date_time/posix_time/ptime.hpp>
#include <boost/date_time/posix_time/posix_time_io.hpp>
#include <boost/format.hpp>
#include <boost/algorithm/string.hpp>
#include <glog/logging.h>
#include <ctime>
#include <cstdlib>
#include <sstream>
#include <mongo/util/version.h>


#include "Core.h"
#include "InformerTemplate.h"
#include "utils/base64.h"
#include "utils/benchmark.h"
#include "HistoryManager.h"
#include "utils/Comparators.h"
#include "utils/GeoIPTools.h"

#include <mongo/bson/bsonobjbuilder.h>


using std::list;
using std::vector;
using std::map;
using std::unique_ptr;
using std::string;
using namespace boost::posix_time;
#define foreach	BOOST_FOREACH

int Core::request_processed_ = 0;
int Core::offer_processed_ = 0;
int Core::social_processed_ = 0;

Core::Core()
    : amqp_initialized_(false), amqp_down_(true), amqp_(0),
    redirect_script_("/redirect")
{
	
    LoadAllEntities();
	InitMessageQueue();
    InitMongoDB();
    time_service_started_ = second_clock::local_time();
}

Core::~Core()
{
    delete amqp_;
}

/** Функтор генерирует токен для предложения ``offer``.
    Возвращает структуру Core::ImpressionItem.

    Токен представляет собой некое уникальное значение, введенное для
    избежания накруток (см. документацию).

    В тестовом режиме токеном является строка "test".
*/
class GenerateToken {
    Params params_;
public:
    GenerateToken(const Params &params) : params_(params) { }
    Core::ImpressionItem operator ()(const Offer &offer)
    {
	Core::ImpressionItem result(offer);

	// Генерируем токен
	if (params_.test_mode_)
	    result.token = "test";
	else {
	    std::ostringstream s;
	    s << std::hex << rand(); // Cлучайное число в шестнадцатиричном
	    result.token = s.str();  // исчислении
	}
	return result;
    }
};


/** Функтор составляет ссылку перенаправления на предложение item.

    Вся строка запроса кодируется в base64 и после распаковки содержит
    следующие параметры:

    \param id        guid рекламного предложения
    \param inf       guid информера, с которого осуществляется переход
    \param url       ссылка, ведущая на товарное предложение
    \param server    адрес сервера, выдавшего ссылку
    \param token     токен для проверки действительности перехода
    \param loc	      адрес страницы, на которой показывается информер
    \param ref	      адрес страницы, откуда пришёл посетитель

    Пары (параметр=значение) разделяются символом \c '\\n' (перевод строки).
    Значения никак не экранируются, считается, что они не должны содержать
    символа-разделителя \c '\\n'.
*/
class GenerateRedirectLink {
    Informer informer_;
    string server_ip_;
    string redirect_script_;
    string location_;
    string referrer_;
public:
    GenerateRedirectLink(const Informer &informer,
			 const string &server_ip,
			 const string &redirect_script,
			 const string &location,
			 const string &referrer)
			     : informer_(informer), server_ip_(server_ip),
			     redirect_script_(redirect_script),
			     location_(location), referrer_(referrer) { }

    void operator ()(Core::ImpressionItem &item) {
	string query = boost::str(
		boost::format("id=%s\ninf=%s\ntoken=%s\nurl=%s\nserver=%s"
			      "\nloc=%s\nref=%s")
		% item.offer.id()
		% informer_.id()
		% item.token
		% item.offer.url()
		% server_ip_
		% location_
		% referrer_
		);
	item.redirect_url = redirect_script_ + "?" + base64_encode(query);
    }
};



/** Обработка запроса на показ рекламы с параметрами ``params``.
	Изменён RealInvest Soft */
std::string Core::Process(const Params &params)
{
	boost::posix_time::ptime startTime, endTime;//добавлено для отладки, УДАЛИТЬ!!!

    request_processed_++;
    time_request_started_ = microsec_clock::local_time();

	
	//startTime = microsec_clock::local_time();
    ProcessMQ();
	//endTime = microsec_clock::local_time();
	//LOG(INFO) << "время обработки очереди ampq = " << (endTime - startTime) << "\n";

	
	
	
	//startTime = microsec_clock::local_time();
    Informer informer(params.informer_);
	if (!informer.valid()) {
	LOG(INFO) << "Invalid informer, returning void. " <<
		RequestDebugInfo(params);
	return std::string();
    }
	//endTime = microsec_clock::local_time();
	//LOG(INFO) << "время получения информера = " << (endTime - startTime) << "\n";

	
	
	
	vector<Offer> offers;

	//получаем список кампаний старым способом.
	//startTime = microsec_clock::local_time();
	list<Campaign> camps;
	list< pair<string,float> > offersIds;
	map< string,float > offersRatingIds;		//RATING NEW!!!!!

	getCampaigns(params, camps);

	//endTime = microsec_clock::local_time();
	//LOG(INFO) << "время получения кампаний старым способом = " << (endTime - startTime) << "\n";
	//LOG(INFO) << "получили список кампаний по геотаргетингу: camps.size()=" << camps.size() << "\n";


	//получаем вектор идентификаторов допустимых для данного пользователя предложений
	//закомментировано для отладки. РАСКОММЕНТИРОВАТЬ!!!!!
	if(!camps.empty()){
		startTime = microsec_clock::local_time();
		offersIds = HistoryManager::instance()->getOffersByUser1(params, camps);
		offersRatingIds = HistoryManager::instance()->getOffersRatingByInformer(params, offersIds);		//RATING NEW!!!!!!!!!!!!!!!!!!!

		endTime = microsec_clock::local_time();
		//LOG(INFO) << "время работы HistoryManager = " << (endTime - startTime) << "\n";
		//LOG(INFO) << "размер списка, полученного от HistoryManager, offersIds.size()=" << offersIds.size() << "\n";
	}
	else{
		LOG(INFO) << "Список кампаний пуст, поэтому запроса к индексу нет.\n";
	}
	//for (auto i=offersIds.begin(); i!=offersIds.end(); i++)
	//{
	//	LOG(INFO) << (*i).first << " " << (*i).second << " ";
	//}
	//LOG(INFO) << "\n";


	////если полученный вектор пуст, используем старый алгоритм, в противном случае используем наш алгоритм
	if (offersIds.size()==0)
	{
		LOG(INFO) << "Сработала старая ветка алгоритма.\n";
		//LOG(INFO) << "country -> " << params.getCountry();
		//LOG(INFO) << "ip -> " << params.getIP();

		// Предложения, которые нужно показать, работает старый алгоритм
		//startTime = microsec_clock::local_time();
		offers = getOffers(informer.capacity(), params, camps);
		//endTime = microsec_clock::local_time();
		//LOG(INFO) << "время работы getOffers + присваивание = " << (endTime - startTime) << "\n";
	} 
	else
	{
		//LOG(INFO) << "Идём по новой ветке.\n";
		//новый алгоритм RealInvest Soft
		//startTime = microsec_clock::local_time();
		//offers = getOffersRIS(offersIds, params, camps);
		offers = getOffersRIS(offersIds, offersRatingIds, params, camps);		//RATING NEW!!!!!
		//endTime = microsec_clock::local_time();

		//LOG(INFO) << "время работы getOffersRIS + присваивание = " << (endTime - startTime) << "\n";
		if (!offers.size())
		{
			//LOG(INFO) << "offers.size()=0, присваиваем 4 пустых РП как в старом алгоритме.\n";
			offers.assign(informer.capacity(), Offer(""));
		}
	}


  
	
	// Если нужно показать только социальную рекламу, а настройках стоит
    // опция "В случае отсутствия релевантной рекламы показывать
    // пользовательский код", то возвращаем пользовательскую заглушку
    //startTime = microsec_clock::local_time();
    if (informer.nonrelevant() == Informer::Show_UserCode && !params.json_) {
	bool all_social = true;
    	for (auto it = offers.begin(); it != offers.end(); it++)  {
	    if (!Campaign(it->campaign_id()).social()) {
		all_social = false;
		break;
    	    }
	}
	if (all_social)
	    return informer.user_code();
    }
	//endTime = microsec_clock::local_time();
	//LOG(INFO) << "время работы блока с информером = " << (endTime - startTime) << "\n";



    // Каждому элементу просмотра присваиваем уникальный токен
	//startTime = microsec_clock::local_time();
    vector<ImpressionItem> items;
    GenerateToken token_generator(params);
    std::transform(offers.begin(), offers.end(), back_inserter(items),
		   token_generator);
	//endTime = microsec_clock::local_time();
	//LOG(INFO) << "время присваивания уникального токена = " << (endTime - startTime) << "\n";

    // Составляем ссылку перенаправления для каждого элемента
	//startTime = microsec_clock::local_time();
    GenerateRedirectLink redirect_generator(informer, server_ip(),
					    redirect_script(),
					    params.location_,
					    params.referrer_);
    std::for_each(items.begin(), items.end(), redirect_generator);
	//endTime = microsec_clock::local_time();
	//LOG(INFO) << "время составления ссылки перенаправления = " << (endTime - startTime) << "\n";

	//LOG(INFO) << "Все этапы до созранения выданных ссылок в базе пройдены.\n";
    // Сохраняем выданные ссылки в базе данных
    try {
		startTime = microsec_clock::local_time();
		list<string> shortTerm = HistoryManager::instance()->getShortHistoryByUser(params);
		list<string> longTerm = HistoryManager::instance()->getLongHistoryByUser(params);
		
		HistoryManager::instance()->updateUserHistory(offers, params);//RealInvest Soft: обновление deprecated (по оставшемуся количеству показов) и краткосрочной истории пользователя (по ключевым словам)
		endTime = microsec_clock::local_time();
		//LOG(INFO) << "время обновления истории пользователя = " << (endTime - startTime) << "\n";
		//LOG(INFO) << "обновили историю пользователя.\n";
		
		startTime = microsec_clock::local_time();
		//int h = atoi(params.getH().c_str());
		//int w = atoi(params.getW().c_str());

		//if (!((w<informer.width() || h<=informer.height()) && items.size()==1))
			markAsShown(items, params, shortTerm, longTerm);
		//else LOG(INFO) << "Log not updated!";
		endTime = microsec_clock::local_time();
		//LOG(INFO) << "время занесения данных в mongo = " << (endTime - startTime) << "\n";
		//LOG(INFO) << "Занесли даннные в базу mongo.\n";
    } catch (mongo::DBException &ex) {
	LOG(ERROR) << "DBException during markAsShown(): " << ex.what();
    }

    // Возвращаем отформатированный информер
    if (params.json_)
	return OffersToJson(items);
    else
	return OffersToHtml(items, offersRatingIds , params);
}







/** 
    Алгоритм работы таков:

	-#  Получаем рекламные кампании, которые нужно показать в этот раз.
	    Выбор кампаний происходит случайно, но с учётом веса. На данный момент
        вес всех кампаний одинаков. Со временем можно сделать составной вес,
        который включал бы в себя цену за клик, CTR и т.д. (расчёт веса
        предварительно производится внешним скриптом).
        .
	-#  Для каждого "места", которое должно быть занято определённой
	    кампанией (п. 1) выбираем товар из этой кампании. Товар также
	    выбирается случайно, но с учётом веса, включающего в себя CTR и др.
	    (также расчитывается внешним скриптом). На данный момент все товары
        равны.
        .
	-#  При малом кол-ве предложений случайное распределение может давать
	    одинаковые элементы в пределах одного информера. Поэтому после
	    получения предложения на п.2, мы проверяем его на уникальность в
	    пределах информера, и если элемент является дубликатом,
	    предпринимаем ещё одну попытку получить предложение. Во избежание
	    вечных циклов, количество попыток ограничивается константой
	    \c Remove_Duplicates_Retries. Увеличение этой константы ведёт к
	    уменьшению вероятности попадания дубликатов, но увеличивает
	    время выполнения. Кроме того, удаление дубликатов меняет
	    весовое распределение предложений. \n
        .
        Иногда удалять дубликаты предложений в пределах кампании недостаточно.
        Например, мы должны показать две кампании. Первая из них содержит всего
        одно предолжение, вторая -- сто. Может случиться, что три места на
        информере будут принадлежать первой кампании. Понятно, что сколько бы
        попыток выбрать "другой" товар этой кампании, у нас ничего не выйдет
        и возникнет дубликат. Поэтому, после \c Remove_Duplicates_Retries
        попыток выбора предложения будет выбрана другая кампания, и цикл
        повториться. Количество возможных смен кампаний задаётся константой
        \c Change_Campaign_Retries.
        .
	-#  Предложения, указанные в \c params.exluded_offers, по возможности
	    исключаются из просмотра. Это используется в прокрутке информера.
 */
vector<Offer> Core::getOffers(int count, const Params &params)
{
    vector<Offer> result(count, Offer(""));

    if (!count) {
        LOG(WARNING) << "0 offers requested!";
        return result;
    }

    list<Campaign> camps;
    getCampaigns(params, camps);

    RandomEntity<Campaign> random_campaigns;
    for (auto it = camps.begin(); it != camps.end(); it++) {
        if (!Offers::x()->offers_by_campaign(*it).empty())
            random_campaigns.add(*it, 1);
    }

    try {
        for (int i = 0; i < count; i++)
            result[i] = 
                _get_one_offer(result, random_campaigns,
                               params.excluded_offers_);

    } catch (RandomEntity<Offer>::NoItemsException) {
        LOG(WARNING) << "RandomEntity<Offer>::NoItemsException. "
                     << RequestDebugInfo(params);
        return result;
    } catch (RandomEntity<Campaign>::NoItemsException) {
        LOG(WARNING) << "RandomEntity<Campaign>::NoItemsException. "
                     << RequestDebugInfo(params);
        return result;
    }

    return result;
}
//добалено RealInvest Soft
vector<Offer> Core::getOffers(int count, const Params &params, const list<Campaign>& camps)
{
	vector<Offer> result(count, Offer(""));
	
	
	if (!count) {
		LOG(WARNING) << "0 offers requested!";
		return result;
	}

	RandomEntity<Campaign> random_campaigns;
	for (auto it = camps.begin(); it != camps.end(); it++) {
		if (!Offers::x()->offers_by_campaign(*it).empty())
			random_campaigns.add(*it, 1);
	}

	try {
		for (int i = 0; i < count; i++)
			result[i] = 
			_get_one_offer(result, random_campaigns,
			params.excluded_offers_);

	} catch (RandomEntity<Offer>::NoItemsException) {
		LOG(WARNING) << "RandomEntity<Offer>::NoItemsException. "
			<< RequestDebugInfo(params);
		return result;
	} catch (RandomEntity<Campaign>::NoItemsException) {
		LOG(WARNING) << "RandomEntity<Campaign>::NoItemsException. "
			<< RequestDebugInfo(params);
		return result;
	}

	return result;
}

/** Возвращает одно предложение, которое можно добавить к результату */
Offer Core::_get_one_offer(const vector<Offer> &result,
                           RandomEntity<Campaign> &random_campaigns,
                           const vector<string> &excluded_offers)
{
    const int Remove_Duplicates_Retries = 5;
    const int Change_Campaign_Retries = 7;
    Offer offer("");
    bool duplicate = true;              // Является ли дупликатом
    int campaign_retry = 0;             // Номер попытки смены кампании

    while (++campaign_retry <= Change_Campaign_Retries && duplicate) {
        Campaign c = random_campaigns.get();
        RandomEntity<Offer> offers = offers_by_campaign(c);
    
        // Удаляем исключённые элементы из списка показа
        for (auto it = excluded_offers.begin();
                  it != excluded_offers.end(); it++) {
            offers.remove(Offer(*it));
        }
        if (!offers.count()) {
            random_campaigns.remove(c);
            continue;
        }
    
        int retry = 0;         // Номер попытки
        do {
            offer = offers.get();
            duplicate = (find(result.begin(), result.end(), offer) !=
                         result.end());
        } while (duplicate && ++retry < Remove_Duplicates_Retries);
    }
    return offer;
}

/** Возвращает в параметре \a out_campaigns список кампаний, подходящих под
    параметры \a params. */
void Core::getCampaigns(const Params &params,
			list<Campaign> &out_campaigns) const
{
    Rules rules;
    rules.set_ip(params.ip_);
    rules.set_informer(params.informer_);
    rules.set_time(params.time_);
    if (!params.country_.empty())
	rules.set_country(params.country_);
    if (!params.region_.empty())
	rules.set_region(params.region_);
    out_campaigns = rules.campaigns();
}




/** Возвращает генератор предложений для кампании campaign,
    кеширует результат.
 */
RandomEntity<Offer> &Core::offers_by_campaign(const Campaign &campaign)
{
    map<Campaign, RandomEntity<Offer> >::iterator it =
	    offers_by_campaign_.find(campaign);
    if (it != offers_by_campaign_.end())
	return it->second;

    // TODO: Весовые распределения товаров
    RandomEntity<Offer> result;
    list<Offer> offers = Offers::x()->offers_by_campaign(campaign);
	//изменено RealInvest Soft. т.к. теперь есть и баннеры, и тизеры, то баннеры не нужно добавлять в результат. это пожелание заказчика - старая ветка должна остаться.
    foreach ( Offer &offer, offers )
	{
		if(!offer.isBanner())
			result.add(offer, 1);
		//RealInvest Soft : надо result.add(offer, offer.rating());
	}

    offers_by_campaign_[campaign] = result;	    // Кешируем результат
    return offers_by_campaign_[campaign];
}


/** Проверка и обработка сообщений MQ.

    Проверяются сообщения со следующими routing key:

    <table>
    <tr>
        <td> \c advertise.# </td>
        <td> уведомления об изменениях в рекламных кампаниях; </td>
    </tr>
    <tr>
        <td> \c informer.# </td>
        <td> уведомления об изменениях в информерах; </td>
    </tr>
    <tr>
	    <td> \c account.# </td>
        <td> уведомления об изменениях в аккаунтах getmyad. </td>
    </tr>
    </table>
	
    На данный момент при получении сообщений \c account.# происходит полная
    перезагрузка всех сущностей (фактически, рестарт). Если это когда-нибудь
    станет узким местом, можно сделать более "тонкую" обработку.

    При получении сообщений \c advertise.# и \c informer.# перезагружено
    будет только то, что нужно (конкретная кампания или информер.

    Чтобы не грузить RabbitMQ лишними проверками, реальное обращение происходит
    не чаще одного раза в две секунды. Во избежание подвисания сервиса в
    случае, когда шлётся сразу много сообщения, после обработки сообщения
    сервис две секунды работает на обработку запросов и не проверяет новые
    сообщения.

    Если при проверке сообщений произошла ошибка (например, RabbitMq оказался
    недоступен) интервал между проверками постепенно увеличивается до пяти
    минут.
*/
bool Core::ProcessMQ()
{
    // Интервал (в секундах) между проверками MQ
    static int check_interval = 0;

    // При возникновении ошибки check_interval постепенно увеличивается до
    // max_check_interval с шагом interval_delta
    const int max_check_interval = 5 * 60;
    const int interval_delta = 5;

    if (!amqp_initialized_)
        return false;
    if (!time_last_mq_check_.is_not_a_date_time() &&
        ((second_clock::local_time() - time_last_mq_check_) <
            seconds(check_interval)))
        return false;
    time_last_mq_check_ = second_clock::local_time();
    if (amqp_down_)
        InitMessageQueue();

    try {
        { // Проверка сообщений advertise.#
            mq_campaign_->Get(AMQP_NOACK);
            AMQPMessage *m = mq_campaign_->getMessage();
            if (m->getMessageCount() > -1) {
                LOG(INFO) << "Message retrieved:";
                LOG(INFO) << "  body:        " << m->getMessage();
                LOG(INFO) << "  routing key: " <<  m->getRoutingKey();
                LOG(INFO) << "  exchange:    " <<  m->getExchange();
                Campaign campaign = Campaign(m->getMessage());
                string logline = boost::str(
                        boost::format("Message (key=%1%, body=%2%, "
                                      "campaign=%3%)")
                        % m->getRoutingKey()
                        % m->getMessage()
                        % campaign.title());
                LogToAmqp(logline);
                ReloadCampaign(campaign);
                time_last_mq_check_ = second_clock::local_time();
                check_interval = 2;
                return true;
            }
        }
        { // Проверка сообщений informer.#
            mq_informer_->Get(AMQP_NOACK);
            AMQPMessage *m = mq_informer_->getMessage();
            if (m->getMessageCount() > -1) {
                LOG(INFO) << "Message retrieved:";
                LOG(INFO) << "  body:        " << m->getMessage();
                LOG(INFO) << "  routing key: " <<  m->getRoutingKey();
                LOG(INFO) << "  exchange:    " <<  m->getExchange();
                Informer informer(m->getMessage());
                string logline = boost::str(
                        boost::format("Message (key=%1%, body=%2%, "
                                      "informer=%3%)")
                        % m->getRoutingKey()
                        % m->getMessage()
                        % informer.title());
                LogToAmqp(logline);
                Benchmark bench("Informer reloaded");
                Informer::loadInformer(informer);
                time_last_mq_check_ = second_clock::local_time();
                check_interval = 2;
                return true;
            }
        }
        { // Проверка сообщений account.#
            mq_account_->Get(AMQP_NOACK);
            AMQPMessage *m = mq_account_->getMessage();
            if (m->getMessageCount() > -1) {
                LOG(INFO) << "Message retrieved:";
                LOG(INFO) << "  body:        " << m->getMessage();
                LOG(INFO) << "  routing key: " <<  m->getRoutingKey();
                LOG(INFO) << "  exchange:    " <<  m->getExchange();
                string logline = boost::str(
                        boost::format("Message (key=%1%, body=%2%")
                        % m->getRoutingKey()
                        % m->getMessage());
                LogToAmqp(logline);
                LoadAllEntities();
                time_last_mq_check_ = second_clock::local_time();
                check_interval = 2;
                return true;
            }
        }
        check_interval = 2;
        amqp_down_ = false;
    } catch (AMQPException &ex) {
        if (!amqp_down_)
            LogToAmqp("AMQP is down");
        amqp_down_ = true;
        if (check_interval + interval_delta < max_check_interval)
            check_interval += interval_delta;
        LOG(ERROR) << ex.getMessage();
    }
    return false;
}


/*
*  Загружает из основной базы данных следующие сущности:
*
*  - рекламные предложения;
*  - рекламные кампании;
*  - информеры.
*
*  Если в кампании нет рекламных предложений, она будет пропущена.
*/
void Core::LoadAllEntities()
{
    Benchmark bench("All entities reloaded");

    Campaign::loadAll();
	//LOG(INFO) << "Загрузили все кампании.\n";
    Offers::x()->loadFromDatabase();
	//LOG(INFO) << "Загрузили все предложения.\n";
    Informer::loadAll();
	//LOG(INFO) << "Загрузили все информеры.\n";

    // Проверяем, нет ли кампаний с 0 предложений
    auto campaigns = Campaign::all();
    for (auto it = campaigns.begin(); it != campaigns.end(); it++)
	if (Offers::x()->offers_by_campaign(*it).empty())
	    LOG(WARNING) << "В кампании " << it->title() << " нет предложений!";

    // Сбрасываем кеш
    offers_by_campaign_.clear();
}


void Core::ReloadCampaign(const Campaign &campaign)
{
    Benchmark bench("Campaign " + campaign.title() + " reloaded");
    Campaign::loadAll();
    Offers::x()->loadByCampaign(campaign);
    offers_by_campaign_.clear();
}


/** \brief  Инициализация очереди сообщений (AMQP).

    Если во время инициализации произошла какая-либо ошибка, то сервис
    продолжит работу, но возможность оповещения об изменениях и горячего
    обновления будет отключена.
*/
void Core::InitMessageQueue()
{
    try {
	// Объявляем точку обмена
	amqp_ = new AMQP;
	exchange_ = amqp_->createExchange();
	exchange_->Declare("getmyad", "topic", AMQP_AUTODELETE);
	LogToAmqp("AMQP is up");

	// Составляем уникальные имена для очередей
	ptime now = microsec_clock::local_time();
	std::string postfix = to_iso_string(now);
	boost::replace_first(postfix, ".", ",");
	std::string mq_advertise_name( "getmyad.advertise." + postfix );
	std::string mq_informer_name( "getmyad.informer." + postfix );
	std::string mq_account_name( "getmyad.account." + postfix );

	// Объявляем очереди
	mq_campaign_ = amqp_->createQueue();
	mq_campaign_->Declare(mq_advertise_name, AMQP_AUTODELETE | AMQP_EXCLUSIVE);
	mq_informer_ = amqp_->createQueue();
	mq_informer_->Declare(mq_informer_name, AMQP_AUTODELETE | AMQP_EXCLUSIVE);
	mq_account_ = amqp_->createQueue();
	mq_account_->Declare(mq_account_name, AMQP_AUTODELETE | AMQP_EXCLUSIVE);

	// Привязываем очереди
	exchange_->Bind(mq_advertise_name, "campaign.#");
	exchange_->Bind(mq_informer_name, "informer.#");
	exchange_->Bind(mq_account_name, "account.#");

	amqp_initialized_ = true;
	amqp_down_ = false;

	LOG(INFO) << "Created ampq queues: " <<
		mq_advertise_name << ", " <<
		mq_informer_name <<  ", " <<
		mq_account_name;
	LogToAmqp("Created amqp queue " + mq_advertise_name);
	LogToAmqp("Created amqp queue " + mq_informer_name);
	LogToAmqp("Created amqp queue " + mq_account_name);

    } catch (AMQPException &ex) {
	LOG(ERROR) << ex.getMessage();
	LOG(ERROR) << "Error in AMPQ init. Feature will be disabled.";
	LogToAmqp("Error in AMQP init: " + ex.getMessage());
	amqp_initialized_ = false;
	amqp_down_ = true;
    }
}



/** Подготовка базы данных MongoDB.
*/
void Core::InitMongoDB()
{
    mongo::DB db("log");
    const int K = 1000;
    const int M = 1000 * K;
    db.createCollection("log.impressions", 250*M, true, 1*M);
}


/** Добавляет в журнал просмотров log.impressions предложения \a items.
    Если показ информера осуществляется в тестовом режиме, запись не происходит.

    Внимание: Используется база данных, зарегистрированная под именем 'log'.
 */
void Core::markAsShown(const vector<ImpressionItem> &items,
		       const Params &params, list<string> &shortTerm, list<string> &longTerm )
{
    if (params.test_mode_)
	return;
    mongo::DB db("log");
	//LOG(INFO) << "writing to log...";

    int count = 0;
	list<string>::iterator it;
	
	mongo::BSONArrayBuilder b1,b2;
	for (it=shortTerm.begin() ; it != shortTerm.end(); it++ )
		b1.append(*it);
	mongo::BSONArray shortTermArray = b1.arr();
	for (it=longTerm.begin() ; it != longTerm.end(); it++ )
		b2.append(*it);
	mongo::BSONArray longTermArray = b2.arr();	
	
    BOOST_FOREACH (const ImpressionItem &i, items) {

	//LOG(INFO) << "  "<<i.offer.id() << "   "<<i.offer.title()<<"  ("<<i.offer.campaign_id()<<")";

	if (i.offer.id().empty()) return;

	std::tm dt_tm;
	dt_tm = boost::posix_time::to_tm(params.time_);
	mongo::Date_t dt( (mktime(&dt_tm)) * 1000LLU);
	Campaign campaign(i.offer.campaign_id());

	//RealInvest Soft: изменено по желанию заказчика. добавлен type и campaignId
	
	mongo::BSONObj keywords = mongo::BSONObjBuilder().
								append("search", params.getUserQueryString()).
								append("ShortTermHistory", shortTermArray).
								append("LongTermHistory", longTermArray).
								obj();

		string country = country_code_by_addr(params.ip_);
		string region = region_code_by_addr(params.ip_);	
					
	mongo::BSONObj record = mongo::BSONObjBuilder().genOID().
								append("dt", dt).
								append("id", i.offer.id()).
								append("title", i.offer.title()).
								append("inf", params.informer_).
								append("ip", params.ip_).
								append("cookie", params.cookie_id_).
								append("social", !(campaign.valid() && !campaign.social())).
								append("token", i.token).
								append("type", i.offer.type()).
								append("campaignId", campaign.id()).
								append("campaignTitle", campaign.title()).
								append("country", (country.empty()?"NOT FOUND":country)).
								append("region", (region.empty()?"NOT FOUND":region)).
								append("keywords", keywords).
								obj();

	db.insert("log.impressions", record, true);
	count++;
	
	offer_processed_ ++;
	if (campaign.social()) social_processed_ ++;
    }
    LOG_IF(WARNING, count == 0 ) << "No items was added to log.impressions!";
}


/** Возвращает данные о состоянии службы */
std::string Core::Status()
{
    // Обработано запросов на момент прошлого обращения к статистике
    static int last_time_request_processed = 0;

    // Время последнего обращения к статистике
    static ptime last_time_accessed;

    time_duration d;

    // Вычисляем количество запросов в секунду
    if (last_time_accessed.is_not_a_date_time())
	last_time_accessed = time_service_started_;
    ptime now = microsec_clock::local_time();
    int millisecs_since_last_access =
	    (now - last_time_accessed).total_milliseconds();
    int millisecs_since_start =
	    (now - time_service_started_).total_milliseconds();
    int requests_per_second_current = 0;
    int requests_per_second_average = 0;
    if (millisecs_since_last_access)
	requests_per_second_current =
		(request_processed_ - last_time_request_processed) * 1000 /
		millisecs_since_last_access;
    if (millisecs_since_start)
	requests_per_second_average = request_processed_ * 1000 /
				      millisecs_since_start;

    last_time_accessed = now;
    last_time_request_processed = request_processed_;

    std::stringstream out;
    out << "<html>\n"
	    "<head><meta http-equiv=\"content-type\" content=\"text/html; "
	    "charset=UTF-8\">\n"
	    "<style>\n"
	    "body { font-family: Arial, Helvetica, sans-serif; }\n"
	    "h1, h2, h3 {font-family: \"georgia\", serif; font-weight: 400;}\n"
	    "table { border-collapse: collapse; border: 1px solid gray; }\n"
	    "td { border: 1px dotted gray; padding: 5px; font-size: 10pt; }\n"
	    "th {border: 1px solid gray; padding: 8px; font-size: 10pt; }\n"
	    "</style>\n"
	    "</head>"
	    "<body>\n<h1>Состояние службы Yottos GetMyAd worker</h1>\n"
	    "<table>"
	    "<tr>"
	    "<td>Обработано запросов:</td> <td><b>" << request_processed_ <<
	    "</b> (" << requests_per_second_current << "/сек, "
	    " в среднем " << requests_per_second_average << "/сек) "
	    "</td></tr>\n"
		"<tr>"
	    "<td>Общее кол-во показов:</td> <td><b>" << offer_processed_ <<
	    "</b> (" << social_processed_ << " из них социальная реклама) "
	    "</td></tr>\n";

    out << "<tr><td>Имя сервера: </td> <td>" <<
	    (getenv("SERVER_NAME")? getenv("SERVER_NAME"): "неизвестно") <<
	    "</td></tr>\n";
    out << "<tr><td>IP сервера: </td> <td>" <<
	    (server_ip_.empty()? "неизвестно": server_ip_) <<
	    "</td></tr>\n";
    out << "<tr><td>Текущее время: </td> <td>" <<
	    second_clock::local_time() <<
	    "</td></tr>\n";

    try {
	mongo::DB db_main;
	out << "<tr><td>Основная база данных:</td> <td>" <<
		db_main.server_host() << "/" << db_main.database() << "<br/>";
	out << "slave_ok = " << (db_main.slave_ok()? "true" : "false");
	if (db_main.replica_set().empty())
	    out << " (no replica set)";
	else
	    out << " (replSet=" << db_main.replica_set() << ")";
	out << "</td></tr>\n";
    } catch (mongo::DB::NotRegistered &) {
	out << "Основная база не определена</td></tr>\n";
    }

	
	
	out << "<tr><td>База данных Redis (краткосрочная история):</td> <td>" <<
		HistoryManager::instance()->getConnectionParams()->redis_short_term_history_host_ << ":";
	out << HistoryManager::instance()->getConnectionParams()->redis_short_term_history_port_;
	out << "(TTL =" << HistoryManager::instance()->getConnectionParams()->shortterm_expire_ << ")<br/>";
	out << "status = " << (HistoryManager::instance()->getDBStatus(1)? "true" : "false");
	out << "</td></tr>\n";
	
	out << "<tr><td>База данных Redis (долгосрочная история):</td> <td>" <<
		HistoryManager::instance()->getConnectionParams()->redis_long_term_history_host_ << ":";
	out << HistoryManager::instance()->getConnectionParams()->redis_long_term_history_port_ <<"<br/>";
	out << "status = " << (HistoryManager::instance()->getDBStatus(2)? "true" : "false");
	out << "</td></tr>\n";	

	out << "<tr><td>База данных Redis (история показов):</td> <td>" <<
		HistoryManager::instance()->getConnectionParams()->redis_user_view_history_host_ << ":";
	out << HistoryManager::instance()->getConnectionParams()->redis_user_view_history_port_ ;
	out << "(TTL =" << HistoryManager::instance()->getConnectionParams()->views_expire_ << ")<br/>";
	out << "status = " << (HistoryManager::instance()->getDBStatus(3)? "true" : "false");
	out << "</td></tr>\n";	

	out << "<tr><td>База данных Redis (констекст страниц):</td> <td>" <<
		HistoryManager::instance()->getConnectionParams()->redis_page_keywords_host_ << ":";
	out << HistoryManager::instance()->getConnectionParams()->redis_page_keywords_port_<<"<br/>";;
	out << "status = " << (HistoryManager::instance()->getDBStatus(4)? "true" : "false");
	out << "</td></tr>\n";
	
	
    try {
	mongo::DB db_log("log");
	out << "<tr><td>База данных журналирования: </td> <td>" <<
		db_log.server_host() << "/" << db_log.database() << "<br/>";
	out << "slave_ok = " << (db_log.slave_ok()? "true" : "false");
	if (db_log.replica_set().empty())
	    out << " (no replica set)";
	else
	    out << " (replSet=" << db_log.replica_set() << ")";
	out << "</td></tr>";

    } catch (mongo::DB::NotRegistered &) {
	out << "База данных журналирования не определена</td></tr>\n";
    }

    out << "<tr><td>Время запуска:</td> <td>" << time_service_started_ <<
	    "</td></tr>" <<
	    "<tr><td>AMQP:</td><td>" <<
	    (amqp_initialized_ && !amqp_down_? "активен" : "не активен") <<
	    "</td></tr>\n";
    out <<  "<tr><td>Сборка: </td><td>" << __DATE__ << " " << __TIME__ <<
	    "</td></tr>";
    out <<  "<tr><td>Драйвер mongo: </td><td>" << mongo::versionString <<
	    "</td></tr>";
    out << "</table>\n";

    std::list<Campaign> campaigns = Campaign::all();
    out << "<p>Загружено <b>" << campaigns.size() << "</b> кампаний: </p>\n";
    out << "<table><tr>\n"
	    "<th>Наименование</th>"
	    "<th>Действительна</th>"
	    "<th>Социальная</th>"
	    "<th>Предложений</th>"
	    "</tr>\n";
    for (auto it = campaigns.begin(); it != campaigns.end(); it++) {
	Campaign c(*it);
	out << "<tr>" <<
		"<td>" << c.title() << "</td>" <<
		"<td>" << (c.valid()? "Да" : "Нет") << "</td>" <<
		"<td>" << (c.social()? "Да" : "Нет") << "</td>" <<
		"<td>" << Offers::x()->offers_by_campaign(c).size() << "</td>"<<
		"</tr>\n";
    }
    out << "</table>\n\n";

    // Журнал сообщений AMQP
    out << "<p>Журнал AMQP: </p>\n"
	    "<table>\n";
    int i = 0;
    for (auto it = mq_log_.begin(); it != mq_log_.end(); it++)
	out << "<tr><td>" << ++i << "</td>"
		"<td>" << *it << "</td></tr>\n";
    out << "<tr><td></td><td>Последняя проверка сообщений: " <<
	    time_last_mq_check_ << "</td><tr>\n"
	    "</table>\n";

    out << "</body>\n</html>\n";

    return out.str();
}


//изменён RealInvest Soft
std::string Core::OffersToHtml(const std::vector<ImpressionItem> &items, map< string,float > &offersRatingIds, const Params &params) const
{
	//Benchmark bench("OffersToHtml закончил свою работу");
    Informer informer(params.informer_);

    // URL получения следующей порции предложений (TODO: Применять UrlEncode)
    stringstream url;
    url << params.script_name_ <<
	    "?scr=" << params.informer_ <<
	    "&show=json";
    if (params.test_mode_)
	url << "&test=true";
    if (!params.country_.empty())
	url << "&country=" << params.country_;
    if (!params.region_.empty())
	url << "&region=" << params.region_;
    url << "&";

	std::string informer_html;

	//RealInvest Soft: для отображения передаётся или один баннер, или вектор тизеров. это и проверяем
	if (!items.empty() && items[0].offer.isBanner())
	{

		// Получаем HTML-код информера
		//LOG(INFO) << "Отображение баннера.\n";

		//string informerCss = "<style type=\"text/css\">#mainContainer {	position: relative;	width: 160px;	height: 600px;	border: 1px solid #000000;	background-color: #c8c642;	overflow: hidden;	border-radius: 5px;}.advBlock {	width: 160px;	height: 600;	border: 0px solid #303030;	float: left;	position: relative;	overflow: hidden;}.advImage {	position: absolute;	width: 160px;	height: 600px;	top: 0px;	left: 0px;	border: 0px solid #adadc7;}.nav {	cursor:pointer;		position: absolute;	width: 11px;	height: 16px;	bottom: 1px;	left: 14px;}.nav a, .nav a:hover, .nav a:link, .nav a:visited, .nav a:active {	font-size: 15px;	text-decoration: none;	/*color: #000000;*/	/*background-color: #ffffff;*/	font-family: Arial, \"Helvetica CY\", \"Nimbus Sans L\", sans-serif;;	display: block;	/*border: 1px solid #000;*/	width: 11px;	}/*.nav a:hover {	color: #ffffff;	background-color: #ffffff;}*/.navr {	cursor:pointer;		position: absolute;	width: 11px;	height: 16px;	bottom: 1px;	left: 1px;}.navr a, .nav a:hover, .navr a:link, .navr a:visited, .navr a:active {	font-size: 15px;	text-decoration: none;	font-family: Arial, \"Helvetica CY\", \"Nimbus Sans L\", sans-serif;;	display: block;	width: 11px;	}#adInfo {	position: absolute;	bottom: 0;	right: 1px;	background-repeat: no-repeat;	overflow:hidden;	background-image: url('http://cdnt.yottos.com/getmyad/logos/colorLogo.gif');	height: 10px;	width: 100px;}	#adInfo a {	width:100%;	height:100%;	display: block;}.c {position: absolute; overflow-x: hidden; overflow-y: hidden; width: 1px; height: 1px;background-color:#000000;}.c1 {position: absolute; overflow-x: hidden; overflow-y: hidden; width: 1px; height: 1px;background-color:#ffffff;}.c2 {position: absolute; overflow-x: hidden; overflow-y: hidden; width: 1px; height: 1px;background-color:#f7f7f;}.b {position: absolute; overflow-x: hidden; overflow-y: hidden; width: 1px; height: 1px;background-color:#000000;}.b1 {position: absolute; overflow-x: hidden; overflow-y: hidden; width: 1px; height: 1px;background-color:#ffffff;}.b2 {position: absolute; overflow-x: hidden; overflow-y: hidden; width: 1px; height: 1px;background-color:#7f7f7f;}</style>";

		informer_html =
			boost::str(boost::format(InformerTemplate::instance()->getBannersTemplate())
			% informer.bannersCss()
			% InformerTemplate::instance()->getSwfobjectLibStr()
			% OffersToJson(items));

		//LOG(INFO) << "После получения кода информера.\n";
	} 
	else
	{
		// Получаем HTML-код информера
		informer_html =
			boost::str(boost::format(InformerTemplate::instance()->getTeasersTemplate())
			% informer.teasersCss()
			% OffersToJson(items)
			% informer.capacity()
			% url.str());
	}

    

    // Для тестового режима добавляем в информер HTML-комментарий со списком
    // кампаний и предложений, которые были доступны для данных параметров,
    // а также настройки подходящих кампаний, время обработки запроса и т.д.
    if (params.test_mode_) {
    long elapsed_usecs = (microsec_clock::local_time() - time_request_started_)
                         .total_microseconds();
	list<Campaign> campaigns;
	getCampaigns(params, campaigns);

	stringstream test_out;
	test_out <<
		"\n<!-- Подходящие кампании: \n";
	for (auto camp = campaigns.begin(); camp != campaigns.end(); camp++) {
	    test_out << "\n" << camp->title() << "\n";

	CampaignShowOptions *opt = CampaignOptionsCache::get(*camp);
	test_out << "Start show time: " << opt->start_show_time() << "\n";
	test_out << "End show time: " << opt->end_show_time() << "\n";

	    std::list<Offer> offers = Offers::x()->offers_by_campaign(*camp);
	    for (auto offer = offers.begin(); offer != offers.end(); offer++) {
		test_out << "    " << offer->title() << "    " << offer->rating() << "\n";
	    }
	}

		test_out <<
		"\n Рейтинги РП для формируемого информера: \n";

		map< string,float >::iterator it;
  		for ( it=offersRatingIds.begin() ; it != offersRatingIds.end(); it++ )
    		test_out << "    " <<(*it).first << "   " << (*it).second << endl;


    test_out << "\nЗатраченное время: " << elapsed_usecs << " µs\n";
	test_out << "-->\n";
	informer_html.append(test_out.str());
    }

    return informer_html;
}


std::string Core::OffersToJson(const vector<ImpressionItem> &items) const
{
    LOG_IF(WARNING, items.empty()) << "No impressions items to show";
    std::stringstream json;
    json << "[";
    for (auto it = items.begin(); it != items.end(); it++) {
		if (it != items.begin())
			json << ",";
		json << "{" <<
			"\"id\": \"" << EscapeJson(it->offer.id()) << "\"," <<
			"\"title\": \"" << EscapeJson(it->offer.title()) << "\"," <<
			"\"description\": \"" << EscapeJson(it->offer.description()) << "\"," <<
			"\"price\": \"" << EscapeJson(it->offer.price()) << "\"," <<
			"\"image\": \"" << EscapeJson(it->offer.image_url()) << "\"," <<
			"\"url\": \"" << EscapeJson(it->redirect_url) << "\"," <<
			"\"token\": \"" << EscapeJson(it->token) << "\"," <<
			"\"rating\": \"" << it->offer.rating() << "\"," <<
			"\"width\": \"" << it->offer.width() << "\"," <<
			"\"height\": \"" << it->offer.height() << "\"" <<
			"}";		
    }

    json << "]";

    return json.str();
}


std::string Core::EscapeJson(const std::string &str)
{
    std::string result;
    for (auto it = str.begin(); it != str.end(); it++) {
	switch (*it) {
	case '\t':
	    result.append("\\t");
	    break;
	case '"':
	    result.append("\\\"");
	    break;
	case '\'':
	    result.append("\\'");
	    break;
	case '/':
	    result.append("\\/");
	    break;
	case '\b':
	    result.append("\\b");
	    break;
	case '\r':
	    result.append("\\r");
	    break;
	case '\n':
	    result.append("\\n");
	    break;
	default:
	    result.append(it, it + 1);
	    break;
	}
    }
    return result;
}


/** Возвращает отладочную информацию про текущий запрос */
std::string Core::RequestDebugInfo(const Params &params) const
{
    std::ostringstream out;
    out << "ip: " << params.ip_ << ", "
	    "inf: " << params.informer_;
    return out.str();
}


/** Помещает сообщение \a message в журнал AMQP */
void Core::LogToAmqp(const std::string &message)
{
    string logline = boost::str(
	    boost::format("%1% \t %2%")
	    % second_clock::local_time()
	    % message);
    mq_log_.push_back(logline);
}




/**Формирование списка РП без учета их рейтинга для конкретного рекламного блока*/
vector<Offer> Core::getOffersRIS(const list< pair<string,float> > &offersIds, const Params &params, const list<Campaign> &camps)
{
	vector<Offer> result;
	
	//LOG(INFO) << "getOffersRIS start\n";

	//LOG(INFO) << result.size() << "\n";
	//1. создаём массив РП по входному списку идентификаторов.
	// сразу же не добавляем баннеры, не подходящие по размеру,
	// сразу же отсортировываем РП внутри одного score
	createVectorOffersByIds(offersIds, result, camps, params);
	//2. выбор РП по новому алгоритму.
	RISAlgorithm(result, params);
	//LOG(INFO) << "getOffersRIS end\n";
	return result;
}

/**Формирование списка РП с учетом их рейтинга для конкретного рекламного блока*/
vector<Offer> Core::getOffersRIS(const list< pair<string,float> > &offersIds, map< string,float > &offersRatingIds, const Params &params, const list<Campaign> &camps)
{
	vector<Offer> result;
	createVectorOffersByIds(offersIds, offersRatingIds, result, camps, params);
	RISAlgorithm(result, params);
	return result;
}



/**
 * Создание вектора из РП по списку идентификаторов РП offersIds. Фильтрация для баннеров происходит здесь же, при создании: если баннер не подходит по размеру для данного РБ (информера), то он в результирующий список не попадает.
 * 
 * \param offersIds - список пар (идентификатор, вес), отсортированный по убыванию веса.
 * \param result - результирующий вектор РП.
 * \param camps - список кампаний, по которым выбирался offersIds.
 * \param params - параметры запроса.
 * 
 * Возвращает вектор из РП, созданный по списку offersIds. РП в результирующем векторе отсортированы по рейтингу в рамках одного веса.
 * 
 * Пример.
 * \code
 * Список offersIds:
 * <a,1.0>
 * <b,1.0>
 * <c,1.0>
 * <e,0.74>
 * <f,0.74>
 * \endcode
 * 
 * Соответствующие пары <идентификатор,рейтинг> (привожу парами, чтоб понятней было; рейтинг берётся из структуры OfferData, т.е. тянется из базы):
 * \code
 * <a,7.44>
 * <b,1.5>
 * <c,54.0>
 * <e,123.7>
 * <f,12.0>
 * \endcode
 * 
 * Другими словами, у РП a рейтинг 7.44, у РП b - 1.5, с - 54.0. Веса соответствия получили такие: у РП a - 1.0, b - 1.0, c - 1.0, e - 0.74, f - 0.74. Веса вычисляются в результате обращения к индексу с учётом весовых коэффициентов, задаваемых вручную и считываемых модулем при его [модуля] загрузке.
 * Для удобства сделаю запись в тройках <идентификатор,вес,рейтинг>:
 * \code
 * <a, 1.0, 7.44>
 * <b, 1.0, 1.5>
 * <c, 1.0, 54.0>
 * <e, 0.74, 123.7>
 * <f, 0.74, 12.0>
 * \endcode
 * Тогда в результате работы метода получим:
 * \code
 * <c, 1.0, 54.0>
 * <a, 1.0, 7.44>
 * <b, 1.0, 1.5>
 * <e, 0.74, 123.7>
 * <f, 0.74, 12.0>
 * \endcode
 * РП отсортированы по убыванию рейтинга в рамках одного веса.
 * 
 * Если список offersIds пуст, то метод в качестве результата выберет все РП из всех РК, находящихся в списке camps, и отсортирует результат по убыванию рейтинга. Поэтому в методе Process если список offersIds пуст, вызывается старая ветка.
 * 
 * 
 */
void Core::createVectorOffersByIds(const list< pair<string,float> > &offersIds, vector<Offer> &result, const list<Campaign> &camps, const Params& params)
{
	//LOG(INFO) << "createVectorOffersByIds start\n";
	//LOG(INFO) << "offersIds.size()=" << offersIds.size() << "\n";
	Informer informer(params.getInformer());
	if (offersIds.size())//если от HistoryManager пришёл непустой список id
	{
		//LOG(INFO) << "список непустой.\n";
		list< pair<string,float> >::const_iterator p = offersIds.begin();
		float curScore = offersIds.begin()->second;
		vector<Offer>::iterator start/* = result.begin()*/;
		vector<Offer>::iterator end;
		int xstart=0;//индекс начала score
		int lenght=0;//длина одного score
		int i=0;
		Offer *curOffer;

		//LOG(INFO) << "перед циклом.\n";
		while(p!=offersIds.end())
		{
			//добавляем оффер к результату.
			//проверка на размер.
			curOffer = new Offer(p->first);
			//LOG(INFO)<<"           offer:"<<curOffer->id()<<"     "<<curOffer->title()<<"   "<<p->second<<endl;
			if (curOffer->valid() && checkBannerSize(*curOffer, informer))
			{
				//если подходит по размеру, добавляем.
				result.push_back(*curOffer);
				//добавили оффер в конец. его score = scores[i]
				//проверяем, вышли ли мы за пределы одного score.

				if (curScore!=p->second)
				{
					//вышли за пределы одного score, надо отсортировать офферы по рейтингу в теперь уже предыдущем score
					end = result.end();
					end--;//end показывает на элемент, который только что добавили
					start = result.begin() + xstart;
					std::sort(start, end, inverseOrderCompare);//отсортировали
					//теперь задаём начало нового (текущего) score
					start = end;//теперь и start показывает на элемент, который только что добавили
					xstart += lenght;
					curScore=p->second;
					lenght = 0;
				}
				else
				{
					lenght++;
				}
			}
			delete curOffer;
			i++;
			p++;
		}
		//LOG(INFO) << "после цикла.\n";
		//LOG(INFO) << "result.size()=" << result.size() << "\n";
		if(result.empty())return;
		//сортировка последнего в result score
		start = result.begin() + xstart;
		std::sort(start, result.end(), inverseOrderCompare);
		//LOG(INFO) << "сортировка последнего score удачна.\n";
	} 
	else
	{
		//если пришёл пустой список, то выбираем все РП кампаний из списка camps
		//LOG(INFO) << "список пустой.\n";
		size_t i = result.size();
		list<Offer> l;
		list<Campaign>::const_iterator c;
		list<Offer>::const_iterator p;
		for (c=camps.begin(); c!=camps.end(); c++)
		{
			l = Offers::x()->offers_by_campaign(*c);
			//добавляем в result. merge если применить, то получим отсортированную последовательность, а нам это не надо здесь
			result.insert(result.end(), l.size(), Offer(""));
			for (p=l.begin(); p!=l.end(); p++,i++)
			{
				result[i] = *p;
			}
		}
		//удаляем excluded
		vector<Offer>::iterator iter;
		for (i=0; i<params.excluded_offers_.size(); i++)
		{
			iter = std::remove_if(result.begin(), result.end(), CExistElementFunctorByType(params.excluded_offers_[i], EOD_ID));
			result.erase(iter, result.end());
		}

		filterOffersSize(result, informer);
		std::sort(result.begin(), result.end(), inverseOrderCompare);
	}

	if (params.json_)
	{
		vector<Offer>::iterator p;
		p = std::remove_if(result.begin(), result.end(), CExistElementFunctorByType("banner", EOD_TYPE));
		result.erase(p, result.end());
	}
	//LOG(INFO) << "result.size()=" << result.size() << "\n";
	//LOG(INFO) << "createVectorOffersByIds end\n";
}

/**
 * Создание вектора из РП по списку идентификаторов РП offersIds с учетом рейтингов РП для данного рекламного блока. 
 * 
 * \param offersIds - список пар (идентификатор, вес), отсортированный по убыванию веса.
 * \param offersRatingIds - множество пар (идентификатор РП, рейтинг), соответствующих значениям рейтинга РП для конкретного РБ
 * \param result - результирующий вектор РП.
 * \param camps - список кампаний, по которым выбирался offersIds.
 * \param params - параметры запроса.
 *  
 * 
 * 
 */
void Core::createVectorOffersByIds(const list< pair<string,float> > &offersIds, map< string,float > &offersRatingIds, vector<Offer> &result, const list<Campaign> &camps, const Params& params)
{
	//LOG(INFO) << "createVectorOffersByIds start\n";
	//LOG(INFO) << "offersIds.size()=" << offersIds.size() << "\n";

	map< string,float >::iterator it;
/*
	LOG(INFO) << "Значения рейтингов РП для текущего РБ:\n";
  for ( it=offersRatingIds.begin() ; it != offersRatingIds.end(); it++ )
    LOG(INFO) << (*it).first << " => " << (*it).second << endl;
*/
	Informer informer(params.getInformer());
	if (offersIds.size())//если от HistoryManager пришёл непустой список id
	{
		
		list< pair<string,float> >::const_iterator p = offersIds.begin();
		float curScore = offersIds.begin()->second;
		vector<Offer>::iterator start/* = result.begin()*/;
		vector<Offer>::iterator end;
		int xstart=0;//индекс начала score
		int lenght=0;//длина одного score
		int i=0;
		Offer *curOffer;

		//LOG(INFO) << "Список выбранных РП:\n";
		while(p!=offersIds.end())
		{
			//добавляем оффер к результату.
			//проверка на размер.
			curOffer = new Offer(p->first);
			it=offersRatingIds.find(curOffer->id());	
			if (it != offersRatingIds.end()) 	
					curOffer->setNewRating(it->second);	

			//LOG(INFO)<<curOffer->id()<<"  "<<curOffer->rating()<<" \t\t "<< p->second<<"  " <<curOffer->title()<<"   "<<endl;
			if (curOffer->valid() && checkBannerSize(*curOffer, informer))
			{
				//если подходит по размеру, добавляем.
				result.push_back(*curOffer);
				//добавили оффер в конец. его score = scores[i]
				//проверяем, вышли ли мы за пределы одного score.

				if (curScore!=p->second)
				{
					//вышли за пределы одного score, надо отсортировать офферы по рейтингу в теперь уже предыдущем score
					end = result.end();
					end--;//end показывает на элемент, который только что добавили
					start = result.begin() + xstart;
					std::sort(start, end, inverseOrderCompare);//отсортировали
					//теперь задаём начало нового (текущего) score
					start = end;//теперь и start показывает на элемент, который только что добавили
					xstart += lenght;
					curScore=p->second;
					lenght = 0;
				}
				else
				{
					lenght++;
				}
			}
			delete curOffer;
			i++;
			p++;
		}
		//LOG(INFO) << "после цикла.\n";
		//LOG(INFO) << "result.size()=" << result.size() << "\n";
		if(result.empty())return;
		//сортировка последнего в result score
		start = result.begin() + xstart;
		std::sort(start, result.end(), inverseOrderCompare);
		//LOG(INFO) << "сортировка последнего score удачна.\n";
	} 
	else
	{
		//если пришёл пустой список, то выбираем все РП кампаний из списка camps
		//LOG(INFO) << "список пустой.\n";
		size_t i = result.size();
		list<Offer> l;
		list<Campaign>::const_iterator c;
		list<Offer>::const_iterator p;
		for (c=camps.begin(); c!=camps.end(); c++)
		{
			l = Offers::x()->offers_by_campaign(*c);
			//добавляем в result. merge если применить, то получим отсортированную последовательность, а нам это не надо здесь
			result.insert(result.end(), l.size(), Offer(""));
			for (p=l.begin(); p!=l.end(); p++,i++)
			{
				result[i] = *p;
			}
		}
		//удаляем excluded
		vector<Offer>::iterator iter;
		for (i=0; i<params.excluded_offers_.size(); i++)
		{
			iter = std::remove_if(result.begin(), result.end(), CExistElementFunctorByType(params.excluded_offers_[i], EOD_ID));
			result.erase(iter, result.end());
		}

		filterOffersSize(result, informer);
		std::sort(result.begin(), result.end(), inverseOrderCompare);
	}

	if (params.json_)
	{
		vector<Offer>::iterator p;
		p = std::remove_if(result.begin(), result.end(), CExistElementFunctorByType("banner", EOD_TYPE));
		result.erase(p, result.end());
	}
	//LOG(INFO) << "result.size()=" << result.size() << "\n";
	//LOG(INFO) << "createVectorOffersByIds end\n";
}


void Core::filterOffersSize(vector<Offer> &result, const string& informerId)
{
	//LOG(INFO) << "filterOffersSize start\n";

	filterOffersSize(result, Informer(informerId));

	//LOG(INFO) << "filterOffersSize end\n";
}

void Core::filterOffersSize(vector<Offer> &result, const Informer& informer)
{
	//LOG(INFO) << "filterOffersSize start\n";

	//размеры баннеров
	vector<Offer>::iterator p = result.begin();
	while(p != result.end())
	{
		if (checkBannerSize(*p, informer))
		{
			p++;
		} 
		else
		{
			p = result.erase(p);
		}

	}

	//LOG(INFO) << "filterOffersSize end\n";
}


bool Core::isOfferInCampaigns(const Offer& offer, const list<Campaign>& camps)
{
	list<Campaign>::const_iterator p = camps.begin();
	while (p != camps.end())
	{
		if (offer.campaign_id()==p->id())
		{
			return true;
		}
		p++;
	}
	return false;
}



bool Core::checkBannerSize(const Offer& offer, const Informer& informer)
{
	if (offer.isBanner())
	{
		if (offer.width() != informer.width() || offer.height() != informer.height())
		{
			return false;
		}
		
	}
	
	return true;
}
/**
 RealInvest Soft. Основной алгоритм.

	(нумерация шагов начинается с номера 2. это осталось исторически и не подлежит изменению. просто первым пунктом раньше шла сортировка, но теперь сортировка идёт при создании РП по списку идентификаторов, т.е. раньше)

	2. если первое РП - баннер - выбрать баннер. конец работы алгоритма.

	3. посчитать тизеры.
	кол-во тизеров < кол-ва мест на РБ -> шаг 12.
	нет -> шаг 14.

	шаг 12 : 
	вычислить средний рейтинг РП типа тизер в последовательности.
	найти первый баннер.
	если баннер есть и его рейтинг > среднего рейтинга по тизерам - отобразить баннер.
	иначе - выбрать все тизеры с дублированием.

	шаг 14 : 
	выбрать самый левый тизер.
	его РК занести в список РК
	искать тизер, принадлежащий не к выбранным РК.
	повторяем, пока не просмотрен весь список.
	если выбранных тизеров достаточно для РБ, показываем.
	если нет - добираем из исходного массива стоящие слева тизеры.	
 */
void Core::RISAlgorithm(vector<Offer> &result, const Params &params)
{
	//LOG(INFO) << "RISAlgorithm start\n";
	//LOG(INFO) << "result.size()=" << result.size() << "\n";

	if (!result.size())
	{
		//такое может быть в случае, если не получили ни одной кампании, и не получили ни одного РП от индекса.
		//LOG(INFO) << "Вектор РП пустой. выходим из алгоритма.\n";
		return;
	}

	////1. сортировка РП по убыванию рейтинга этого нет, т.к. теперь сортируем при создании
	//std::sort(result.begin(), result.end(), inverseOrderCompare);
	//LOG(INFO) << "Сортировка успешна. Этап 1 пройден.\n";
	

	vector<Offer>::iterator p;
	p = result.begin();
	bool all_social = true;
	while(p!=result.end())
	{
		if (!(Campaign((*p).campaign_id()).social()))
		{
			all_social = false;
			break;
		}
		p++;
	}
	
	if (!all_social)
	{
		//LOG(INFO) << "Exists nonsocial offers. Remove social. size before = "<<result.size();
		p = result.begin();
		while(p!=result.end())
		{
			if ((Campaign((*p).campaign_id()).social()))
				result.erase(p);
			else p++; 
		}
		//LOG(INFO) << "                                      size after = "<<result.size();
		//std::remove_if(result.begin(), result.end(), isSocial);
	}
	//else LOG(INFO) << "In array all social offers.";
	
	
	//2. если первый элемент баннер, возвращаем баннер.
	//LOG(INFO)<<"BEFORE social";
	if ( result[0].isBanner() && (!Campaign(result[0].campaign_id()).social()))
	{
		//LOG(INFO)<<"NON social banner";
		p = result.begin();
		p++;
		result.erase(p, result.end());
		return;
	}
	if ( result[0].isBanner() && (Campaign(result[0].campaign_id()).social()) && result.size()==1)
	{
		//LOG(INFO)<<"social banner";
		p = result.begin();
		p++;
		result.erase(p, result.end());
		return;
	}
	//LOG(INFO)<<"AFTER social";
	//LOG(INFO) << "Первый элемент не баннер. Этап 2 пройден.\n";
	
	//3. посчитать тизеры.
	int teasersCount = std::count_if(result.begin(),result.end(),CExistElementFunctorByType("teaser", EOD_TYPE));
	//LOG(INFO) << "Этап 3: кол-во тизеров=" << teasersCount << "\n";

	//кол-во тизеров < кол-ва мест на РБ -> шаг 12.
	//нет -> шаг 14.
	Informer informer(params.informer_);
	//LOG(INFO) << "Этап 3: кол-во мест на РБ=" << informer.capacity() << "\n";


	////----------------добавлено для отладки----------------
	//while(teasersCount > informer.capacity()/2)
	//{
	//	p = result.end();
	//	p--;
	//	result.erase(p);
	//	teasersCount = std::count_if(result.begin(),result.end(),CExistElementFunctorByType("teaser", EOD_TYPE));
	//}
	//LOG(INFO) << "Этап 3: кол-во тизеров=" << teasersCount << "\n";
	////-----------------------------------------------------


	if (teasersCount < informer.capacity())
	{
		//LOG(INFO) << "шаг 12.\n";
		//шаг 12
		//вычислить средний рейтинг РП типа тизер в последовательности.
		double avgTR = mediumRating(result, "teaser");
		//LOG(INFO) << "средний рейтинг тизеров в последовательности=" << avgTR << "\n";
		//найти первый баннер
		p = std::find_if(result.begin(),result.end(), CExistElementFunctorByType("banner", EOD_TYPE));
		//если баннер есть и его рейтинг > среднего рейтинга по тизерам - отобразить баннер
		if (p!=result.end() && (*p).rating() > avgTR)
		{
			result.erase(result.begin(), p);
			p++;
			result.erase(p, result.end());
			return;
		}
		//LOG(INFO) << "баннер не найден или его рейтинг <= среднего рейтинга тизеров\n";
		//иначе - выбрать все тизеры с дублированием
		//т.е. удалить все баннеры и добавлять в конец вектора существующие элементы
		p = std::remove_if(result.begin(), result.end(), CExistElementFunctorByType("banner", EOD_TYPE));
		result.erase(p, result.end());
		int c=0;
		while ((int)result.size() < informer.capacity())
		{
			if (c>=teasersCount)
			{
				c=0;
			}
			result.push_back(result[c]);
			c++;
		}
		//LOG(INFO) << "выбрали тизеры с дублированием\n";
		//LOG(INFO) << "шаг 12 end.\n";
	} 
	else
	{
		//шаг 14 [тов. Каштанов: шаг 14 рассматриваем только при неравенстве. при равенстве всё равно выведутся все]
		if (teasersCount > informer.capacity())
		{
			//LOG(INFO) << "шаг 14.\n";
			//шаг 14
			//удаляем все баннеры, т.к. с ними больше не работаем
			p = std::remove_if(result.begin(), result.end(), CExistElementFunctorByType("banner", EOD_TYPE));
			result.erase(p, result.end());
			//LOG(INFO) << "шаг 14 : удалили все баннеры.\n";
			//LOG(INFO) << "result.size()=" << result.size() << "\n";

			//выбрать самый левый тизер.
			//его РК занести в список РК
			//искать тизер, принадлежащий не к выбранным РК.
			//повторяем, пока не просмотрен весь список.
			//если выбранных тизеров достаточно для РБ, показываем.
			//если нет - добираем из исходного массива стоящие слева тизеры.	


			list<string> camps;
			//list<string> teasers;
			vector<Offer> newResult;

			p = result.begin();
			while(p!=result.end())
			{
				//если кампания тизера не занесена в список, выбираем тизер, выбираем кампанию
				if(!isStrInList((*p).campaign_id(), camps))
				{
					newResult.push_back((*p));
					//teasers.push_back((*p).id());
					camps.push_back((*p).campaign_id());
				}
				p++;
			}
			//LOG(INFO) << "шаг 14 : выбрали тизеры из неповторяющихся кампаний.\n";
			//LOG(INFO) << "teasers.size()=" << teasers.size() << "\n";
			//LOG(INFO) << "newResult.size()=" << newResult.size() << "\n";
			//LOG(INFO) << "camps.size()=" << camps.size() << "\n";

			//если выбрали тизеров меньше, чем мест в информере, добираем тизеры из исходного вектора
			p = result.begin();
			while(p!=result.end() && ((int)newResult.size() < informer.capacity()))
			{//доберём всё за один проход, т.к. result.size > informer.capacity
				//пробуем сначала добрать без повторений.
				if(!isOfferInVector((*p), newResult))
					newResult.push_back((*p));
				p++;
			}
			//LOG(INFO) << "шаг 14 : после попытки добора без повторений:" << " newResult.size()=" << newResult.size() << ".\n";
			
			//теперь, если без повторений добрать не получилось, дублируем тизеры.
			p = result.begin();
			while(p!=result.end() && ((int)newResult.size() < informer.capacity()))
			{//доберём всё за один проход, т.к. result.size > informer.capacity
				//пробуем сначала добрать без повторений.
				newResult.push_back((*p));
				p++;
			}
			
			//LOG(INFO) << "шаг 14 : добрали тизеры, если не хватало.\n";
			//LOG(INFO) << "teasers.size()=" << teasers.size() << "\n";
			//LOG(INFO) << "newResult.size()=" << newResult.size() << "\n";

			
			result.assign(newResult.begin(), newResult.begin()+informer.capacity());
			//LOG(INFO) << "шаг 14 : из исходного вектора удалили тизеры, которых нет в списке отобранных.\n";
			//LOG(INFO) << "result.size()=" << result.size() << "\n";
			//LOG(INFO) << "шаг 14 end.\n";
		}
	}
	//LOG(INFO) << "RISAlgorithm end\n";
}




float Core::mediumRating(const vector<Offer>& vectorOffers, const string &typeOfferStr)
{
	float summRating=0;
	int countElements = 0;
	vector<Offer>::size_type i;

	for(i=0; i < vectorOffers.size();i++)
	{
		if(vectorOffers[i].type() == typeOfferStr)
		{
			summRating += vectorOffers[i].rating();
			countElements++;
		}
	}

	return summRating/countElements;
}

bool Core::isSocial (Offer& i) { return Campaign(i.campaign_id()).social(); }
