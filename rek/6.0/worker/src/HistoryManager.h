/**
 Класс добавлен RealInvest Soft
 */
#pragma once

#include <string>
#include <vector>
#include <list>
#include "DBAccessor/DBWrapper.h"
#include "DBAccessor/DBConnectionParams.h"
#include "FullTextSearcher/SearcherWrapper.h"
#include "Params.h"
#include "Offer.h"
#include "Campaign.h"
#include "utils/benchmark.h"

#include <glog/logging.h>

using namespace std;


/** \brief Класс, через который класс Core получает доступ к истории пользователя и осуществляет полнотекстовый поиск.

	Класс реализован по шаблону Singleton (Одиночка).


*/
class HistoryManager
{
private:
	HistoryManager(){}
protected:
	redisDB::DBWrapper accessor;	///< Объект доступа к базам данных Redis.
	SearcherWrapper searcher;		///< Объект доступа к библиотеке полнотекстового доступа.
	DBConnectionParams connParams;	///< Параматеры подключения к базам данных Redis.
	Weights w;						///< Весовые коэффициенты для задания приоритета историй при поиске.
public:
	/** \brief  Метод получения экземпляра класса 

		Метод создает единственный экземпляр класса при первом обращении. При повторных обращениях 
		возвращается ссылка на уже созданный объект.
	*/	
	static HistoryManager* instance()
	{
		static HistoryManager *ob = new HistoryManager;
		return ob;
	}

	/** \brief  Инициализация подключения к базам данных Redis 

		\param params     		параметры подключения
	*/
	int initDB(DBConnectionParams &params)
	{
		connParams = params;
		return accessor.InitConnection(params);
	}

	/** \brief  Возвращает параметры подключения к базам данных Redis 

	*/
	DBConnectionParams* getConnectionParams()
	{
		return &connParams;
	}
	
	/** \brief  Возвращает статус подключения к одной из баз данных Redis. 

		\param t     		тип базы данных </BR>
		
		Возможные значения:</BR>
		1 - база данных краткосрочной истории</BR>
		2 - база данных долгосрочной истории</BR>
		3 - база данных истории показов</BR>
		
		При некорректно заданном параметре метод вернет -1.
	*/	
	int getDBStatus(int t)
	{
		switch(t){
			case 1: return accessor.getShortTermStatus();
			case 2: return accessor.getLongTermStatus();
			case 3: return accessor.getViewHistoryStatus();
			case 4: return accessor.getPageKeywordsStatus();
			default: return -1;
		}
	}
	
	/** \brief  Инициализация весов для задания приоритететов групп рекламных предложений при формировании списка предложений к показу 

		\param range_priority_banners     	вес рекламных предложений типа "баннер по показам"
		\param range_query 					вес рекламных предложений, соответствующих запросу с поисковика
		\param range_shot_term 				вес рекламных предложений, соответствующих краткосрочной истории
		\param range_long_term 				вес рекламных предложений, соответствующих долгосрочной истории
		\param range_context 				вес рекламных предложений, соответствующих контексту страницы
		\param range_on_places 				вес рекламных предложений, типа "реклама на места размещения"		
		
	*/	
	void initWeights(
		float range_priority_banners, 
		float range_query, 
		float range_shot_term, 
		float range_long_term, 
		float range_context, 
		float range_on_places
		)
	{
		w.range_priority_banners = range_priority_banners;
		w.range_query = range_query;
		w.range_shot_term = range_shot_term;
		w.range_long_term = range_long_term;
		w.range_context = range_context;
		w.range_on_places = range_on_places;
	}
	
/** \brief  Инициализация весов для задания приоритететов групп рекламных предложений при формировании списка предложений к показу 

		\param range_priority_banners     	вес рекламных предложений типа "баннер по показам"
		\param range_query 					вес рекламных предложений, соответствующих запросу с поисковика
		\param range_shot_term 				вес рекламных предложений, соответствующих краткосрочной истории
		\param range_long_term 				вес рекламных предложений, соответствующих долгосрочной истории
		\param range_context 				вес рекламных предложений, соответствующих контексту страницы
		\param range_on_places 				вес рекламных предложений, типа "реклама на места размещения"		
		
	*/	
	void initWeights(
		const string &range_priority_banners, 
		const string &range_query, 
		const string &range_shot_term, 
		const string &range_long_term, 
		const string &range_context, 
		const string &range_on_places)
	{
		w.range_priority_banners = atof(range_priority_banners.c_str());
		w.range_query = atof(range_query.c_str());
		w.range_shot_term = atof(range_shot_term.c_str());
		w.range_long_term = atof(range_long_term.c_str());
		w.range_context = atof(range_context.c_str());
		w.range_on_places = atof(range_on_places.c_str());
	}


	/** \brief Получение идентификаторов РП от индекса lucene.
	 *
	 * Получение идентификаторов РП от индекса lucene.
	 * \param params - параметры запроса.
	 * \param campaigns - список кампаний, отобранных для показа.
	 * 
	 * Возвращает список пар (идентификатор,вес), отсортированный по убыванию веса.
	 * 
	 * В этом методе происходит обращение к redis за историей пользователя и отбор идентификаторов РП из индекса CLucene.
	 */
	list< pair<string, float> > getOffersByUser1(const Params& params, list<Campaign>& campaigns)
	{
		//Benchmark bench("\nвремя обращения к HistoryManager за списом идентификаторов РП (HistoryManager::getOffersByUser1) ");
		//получить контекст страницы от DBAccessor
		//vector<string> pageContext = accessor.getContextByUrl(params.getLocation());

		//uint64_t strr = Misc::currentTimeMillis();

		vector<string> pageContext;

		//получить историю пользователя от DBAccessor
		//LOG(INFO) << "перед получением userHistory" << "\n";
		//UserHistory * uh = accessor.getUserHistoryById(params.getIP());
		UserHistory * uh = accessor.getUserHistoryByIdAndLocation(params.getIP(), params.getLocation());	//NEW!!!!!!!!!!!!!!!!!!!!


		//LOG(INFO) << "после получения userHistory" << "\n";

		//// добавляем идентификаторы excluded РП в список deprecatedOffers
		uh->getDeprecatedOffers().insert(uh->getDeprecatedOffers().end(), params.excluded_offers_.begin(), params.excluded_offers_.end());
		//LOG(INFO)<<uh->historyToLog();
		////поиск
		//LOG(INFO) << "getOffersByUser: перед f1(...)\n";


		//uint32_t srch = (int32_t)(Misc::currentTimeMillis() - strr);
		//LOG(INFO) << "\nAction before search took: " << srch << " ms.\n"; 


		list< pair<string, float>  > result = searcher.f1(params.getUserQueryString(), *uh, pageContext, params.getInformer(), campaigns, w);

		delete uh;

		return result;
		//return list< pair<string, float> >();
	}
	
		/** \brief Получение краткосрочной истории пользователя.
	 *
	 * \param params - параметры запроса.
	 */
	list<std::string> getShortHistoryByUser(const Params& params)
	{

		UserHistory * uh = accessor.getUserHistoryById(params.getIP());
		list <std::string> temp = uh->getShortHistory();
		delete uh;
		return temp;

	}
		/** \brief Получение долгосрочной истории пользователя.
	 *
	 * \param params - параметры запроса.
	 */
	list<std::string> getLongHistoryByUser(const Params& params)
	{

		UserHistory * uh = accessor.getUserHistoryById(params.getIP());
		list <std::string> temp = uh->getLongHistory();
		delete uh;
		return temp;

	}	
	/** Обновление short и deprecated историй пользователя. */
	/** \brief  Обновление краткосрочной истории пользователя и истории его показов. 

		\param offers     		вектор рекламных предложений, выбранных к показу
		\param params			параметры, переданный ядру процесса   
	*/
	bool updateUserHistory(const vector<Offer>& offers, const Params& params)
	{
		//Benchmark bench("\nвремя обновления историй пользователя (HistoryManager::updateUserHistory) ");
		//LOG(INFO) << "updateUserHistory start\n";
		accessor.updateDeprecatedUserHistory(params.getIP(), offers);
		//LOG(INFO) << "updateUserHistory middle\n";
		accessor.updateShortHistory(params.getIP(), params.getUserQueryString());
		//LOG(INFO) << "updateUserHistory end\n";
		return true;
	}
};