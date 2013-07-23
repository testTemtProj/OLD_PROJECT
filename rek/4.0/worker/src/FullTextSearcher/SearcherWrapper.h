#pragma once
#include<string>
#include<vector>
#include <list>
#include <algorithm>
#include "XXXSearcher.h"
#include "../Campaign.h"
#include "../UserHistory.h"


#include <glog/logging.h>

using namespace std;

/** \brief Функция, сравнивающая пары a и b по возрастанию веса. Возвращает a.second < b.second. */
bool rigthOrderPairCompare(const pair<string, float>  &a, const pair<string, float>  &b);
/** \brief Функция, сравнивающая пары a и b по убыванию веса. Возвращает a.second > b.second. */
bool inverseOrderPairCompare(const pair<string, float>  &a, const pair<string, float>  &b);

/** \brief Структура, хранящая веса для всех шести запросов к lucene */
struct Weights{
public:
	float range_priority_banners;///< запрос 1 по "крутым" баннерам
	float range_query;///< запрос 2 по query
	float range_shot_term;///< запрос 3 по shortHistory
	float range_long_term;///< запрос 4 по longHistory
	float range_context;///< запрос 5 по контексту страницы
	float range_on_places;///< запрос 6 - РП по размещению

	Weights(){
		range_priority_banners = 1.0;
		range_query = 1.0;
		range_shot_term = 1.0;
		range_long_term = 1.0;
		range_context = 1.0;
		range_on_places = 1.0;
	}
};

/** \brief Класс-обёртка работы с CLucene. 
 *
 * Класс добавлен RealInvest Soft.
 * 
 * Построение индекса производится вне модуля. Модуль лишь читает индекс.\n
 * Индекс располагается на жёстком диске.\n
 * Индекс хранит документы. В качестве документов выступают рекламные предложения из основной базы данных, с которой работает модуль. В индекс занесены (проиндексированы) следующие поля:
 * \code
 * guid - идентификатор РП.
 * keywords - ключевые слова, закреплённые за РП.
 * minus_words - минус-слова, закреплённые за РП.
 * informer_ids - идентификатор информера, за которым закреплено РП.
 * campaign_id - идентификатор кампании, к которой принадлежит данное РП.
 * type - тип РП.
 * \endcode
 * 
 * Обращаясь на определённом языке запросов к индексу с помощью инструментов CLucene можно извлечь документы, удовлетворяющие условиям запроса.\n
 * Перевод нужных запросов на язык Lucene - это и есть предназначение этого класса.
 * 
 * Запросов к индексу всего 6 (реально - 5).
 * \see Методы f1
 * 
 * Запросы к индексу:\n
 * 1)запрос по "крутым" баннерам: выбор РП типа баннер, которые по настройкам должны показываться или на всех информерах, или на информере, для которого модуль обрабатывает запрос. Кроме того, выбираемые РП должны принадлежать к выбранным для показа рекламным кампаниям и не должны принадлежать ко множеству предложений, не подлежащих отбору.\n
 * 2)запрос по строке запроса из поисковика (если пользователь перешёл на сайт партнёрской сети из поисковика): выбор РП, у которых в ключевых словах и/или точных фразах встречается содержимое строки запроса, а в минус-словах его нет. Кроме того, выбираемые РП должны принадлежать к выбранным для показа рекламным кампаниям и не должны принадлежать ко множеству предложений, не подлежащих отбору.\n
 * 3)запрос по краткосрочной истории пользователя (краткосрочная история - предыдущие 2 строки запроса): выполняются точно такие же запросы, как в запросе 2, но для каждой строки запроса из истории. Т.е. в 2 выполняется один запрос, а в 3 - несколько (не более 2-х) таких же запросов с точностью до содержимого строки. Результаты объединяются в один.\n
 * 4)запрос по longHistory: выбор РП, у которых в ключевых словах встречается содержимое из longHistory, однако в минус-словах его [содержимого] нет. Кроме того, выбираемые РП должны принадлежать к выбранным для показа рекламным кампаниям и не должны принадлежать ко множеству предложений, не подлежащих отбору.\n
 * 5)запрос по контексту страницы. Не выполняется, т.к. модуль пока что с контекстом не работает.\n
 * 6)запрос РП на места размещения: выбор РП типа тизер, которые по настройкам должны показываться или на всех информерах, или на информере, для которого модуль обрабатывает запрос. Кроме того, выбираемые РП должны принадлежать к выбранным для показа рекламным кампаниям и не должны принадлежать ко множеству предложений, не подлежащих отбору.\n
 * 
 */
class SearcherWrapper
{
protected:
	XXXSearcher *searcher;///< исполнитель запросов к индексу.
	string dirNameOffer;///< имя папки, в которой расположен индекс. Вбито в код: "/var/www/index".
	string dirNameInformer;
	char ch;///< символ '"', для удобства написания кода.
	char exCh;///< этим символом начинается и заканчивается каждая точная фраза.
public:
	SearcherWrapper()
	{
		
		dirNameOffer = "/var/www/indexOffer";
		dirNameInformer = "/var/www/indexInformer";
		//LOG(INFO) << "папка, в которой расположен индекс: " << directoryName << "\n";
		searcher = new XXXSearcher(dirNameOffer, dirNameInformer);
		//LOG(INFO) << "searcher создан.\n";
		ch = '"';
		exCh = '$';
	}
	~SearcherWrapper()
	{
		delete searcher;
	}

	
	void setLuceneIndexParams(string &folder_offer, string &folder_informer)
	{
		dirNameOffer = folder_offer;
		dirNameInformer = folder_informer;	
		searcher-> setLuceneIndexParams(dirNameOffer , dirNameInformer );	
		LOG(INFO)<<"Lucene index params: offer_index =  "<<dirNameOffer <<" informer_index = "<<dirNameInformer;
	}

protected:
	
	/** \brief Метод создания запроса к индексу.
	 
	 Конструирует запрос к индексу.

	 @param qpart Сама суть запроса, без обязательных условий на отобранные кампании и предложения, не подлежащие отбору из индекса.
	 @param campaingsString Список отобранных кампаний. РП должны отбираться только из этих кампаний.
	 @param deprecatedString Список РП, не подлежащих отбору из индекса.
	 
	 Примечания: campaingsString идёт уже в "готовом" виде, т.е. \code +campaign_id:(кампания1 кампания2 кампания3) \endcode
	 \n deprecatedString - просто как список идентификаторов, в "готовый" вид он приводится уже внутри метода. Это сделано для возможности добавления РП, не подлежащих отбору из индекса, во время выполнения метода, динамически.\n А список кампаний меняться не будет, он задаётся один раз, поэтому он приходит уже в "готовом" виде. */
	string constructQuery(const string &qpart, const string &campaingsString, const string &deprecatedString)
	{
		//LOG(INFO) << "|" << qpart << "|" << campaingsString << "|" << deprecatedString << "|\n";
		if(qpart.empty() )
		{
			//LOG(INFO) << "нет данных для запроса.\n";
			return string();
		}
		string qstr = campaingsString + " "+qpart;
                  
		//if (!deprecatedString.empty())
		//{
		//	qstr += " -guid:(" + deprecatedString + ")";
		//}
		qstr.push_back(0);
		//LOG(INFO) << "запрос = " << "|" << qstr << "|\n";
		return qstr;
	}

	string constructFilter(const string &deprecatedString)
	{
		string qstr = "+type:(teaser banner)   ";
		if(deprecatedString.empty() )
		{
			//qstr.push_back(0);
			//return qstr;
			LOG(INFO)<<"deprecated history empty";
			return "";
		}
		else
		{
			qstr += " -(" + deprecatedString + ") ";
		}
		qstr.push_back(0);
		
		return qstr;
	}

	
	/** \brief Перевод содержимого списка в строку через пробел. 
	 @param l Список строк.
	 @return Строку, сотоящую из строк, содержащихся в списке, перечисленных через пробел.
	 
	 Пример:
	 \code
	 Список l:
	 <str1>
	 <str2>
	 <str3>
	 
	 Выход метода: "str1 str2 str3"
	 \endcode
	  
	 */
	string listOfStringsToString(const list<string>& l)
	{
		string str;
		list<string>::const_iterator p;
		for (p=l.begin(); p!=l.end(); p++)
		{
			if (!p->empty())
			{
				str += (*p + " ");
			}
		}
		//if (!str.empty()) str += "aaa";
		return str;
	}

	string listOfStringsToStringLimit(const list<string>& l)
	{
		string str;
		list<string>::const_iterator p;
		size_t count = l.size();
		if (count == 56 || count==111 || count==165 || count == 166) return str;
		//if ((l.size()-1)%55==0) return str;
		for (p=l.begin(); p!=l.end(); p++)
		{
			if (!p->empty())
			{
				str += (*p + " ");
			}
		}
		//if (!str.empty()) str += "aaa";
		return str;
	}

	/** \brief Перевод содержимого списка (первого элемента в паре) в строку через пробел. 
	@param l Список пар <строка, вес>.
	@return Строку, сотоящую из строк, содержащихся в первых элементах в парах в списке, перечисленных через пробел.

	Пример:
	\code
	Список l:
	<str1,2.2>
	<str2,0.75>
	<str3,10.4>

	Выход метода: "str1 str2 str3"
	\endcode

	 */
	string listOfStringsToString(const list< pair<string, float>  >& l)
	{
		string str;
		list< pair<string, float>  >::const_iterator p;
		for (p=l.begin(); p!=l.end(); p++)
		{
			if (!p->first.empty())
			{
				str += (p->first + " ");
			}
		}
		
		return str;
	}

	/** \brief Метод получения списка кампаний в "готовом" виде.
	 
	 Т.е. чтоб строку можно было просто вставить в запрос к индексу без дополнительных действий.

	 @param campaigns Список кампаний, отобранных для показа.
	 @return Строку, содержащую список кампаний campaigns, готовую для непосредственной вставки в запрос к индексу.
	 
	 Пример:
	 \code
	 Список campaigns:
	 <кампания1>
	 <кампания2>
	 <кампания3>
	 
	  Выход метода: "+campaign_id:(кампания1 кампания2 кампания3)"
	 \endcode
	 */
	string getCampaignsString(const list<Campaign>& campaigns)
	{
		// +campaign_id:(все значения из списка кампаний)
		if (campaigns.empty())
		{
			return string();
		}
		string str = "+campaign_id:(";
		list<Campaign>::const_iterator p;

		for (p=campaigns.begin(); p!=campaigns.end(); p++)
		{
			str += (p->id()+ " ");
	
		}
		str += ") ";
		return str;
		//return "+campaign_id:(6aa5383e-5ddb-4eb5-b693-d96acd17409b 6fcec5d5-3976-4ae0-a0dd-11056762af80 bd15f42a-643b-4d64-b24b-9b14d6b02095)";
		//return "";


	}

	/**
	 * 1. запрос по "крутым" баннерам.
	 * +informer_ids:(ALL наш_информер) 
	 * +abcde 
	 * +exactly_phrases:("abcde")
	 * +minus_words:(abcde)
	 * +type:banner
	 * // +campaign_id:(все значения из списка кампаний)
	 * // -guid:(deprecatedOffers)
	 */
	string getPriorityBannersString(const string& informerId)
	{
		if (informerId.empty())
		{
			return string();
		}
		string str = "+informer_ids:(all OR " + informerId + ") +abcde +exactly_phrases:(\"abcde\") +minus_words:(abcde) +type:banner";
		//string str = "informer_ids:all AND keywords:abcde";
		//string str = "type:banner AND informer_ids:(" + informerId + ") AND keywords:abcde AND exactly_phrases:(\"abcde\") AND minus_words:(abcde) ";

              //string str="";
		return str;
	}

	string getPriorityBannersString1(const string& informerId, const string& topics)
	{
		if (informerId.empty())
		{
			return string();
		}
		string str = "+informer_ids:(all OR " + informerId + ") +abcde +exactly_phrases:(\"abcde\") +minus_words:(abcde) +type:banner ";
		if (!topics.empty())
		{
			str += " +topic_ids:(" + topics + ") ";
		}
		

              //string str="";
		return str;
	}

	

	/**
	 * 2. запрос по query - по строке запроса из поисковика.
	 * +(keywords:(query)
	 * exactly_phrases:("$query$"))
	 * -minus_words:(query)
	 * // +campaign_id:(все значения из списка кампаний)
	 * // -guid:(deprecatedOffers)
	 */
	string getQueryString(const string& query, const string& informerId)
	{
		if (query.empty())
		{
			return string();
		}
		string str = "+informer_ids:(all " + informerId + ") +(keywords:(" + query + ") keywords_eng:(" + query + ") exactly_phrases:(" + ch + exCh + query + exCh + ch + ")) -minus_words:(" + query + ") ";
		//string str = "(keywords:(" + query + ") OR keywords_eng:(" + query + ") OR exactly_phrases:(" + ch + exCh + query + exCh + ch + ")) AND NOT minus_words:(" + query + ") ";
		return str;
	}

	string getQueryString1(const string& query, const string& informerId, const string& newquery)
	{
		if (query.empty())
		{
			return string();
		}
		string str = "+informer_ids:(all " + informerId + ") +(keywords:(" + query + ") keywords_eng:(" + query + ") exactly_phrases:(" + ch + exCh + query + exCh + ch + ")) ";
		//string str = "(keywords:(" + query + ") OR keywords_eng:(" + query + ") OR exactly_phrases:(" + ch + exCh + query + exCh + ch + ")) AND NOT minus_words:(" + query + ") ";
		if (!newquery.empty())
		{
			str = str+" -minus_words:(" + newquery + ") ";
		}
		

		return str;
	}


	/**
	 * 4. longHistory - только по keywords и minus_words и -результат 2 и 3.
	 * +keywords:(longHistory)
	 * -minus_words:(longHistory)
	 * // +campaign_id:(все значения из списка кампаний)
	 * // -guid:(deprecatedOffers результат2 результат3)
	 */
	string getLongHistoryString(const list<string>& longHistory)
	{
		string lH = listOfStringsToString(longHistory);
		if (lH.empty())
		{
			return string();
		}
		string str = "(keywords:(" + lH + ")  keywords_eng:(" + lH + "))  -minus_words:(" + lH + ") ";
		return str;
	}

	/**
	 * 6. РП на места.
	 * +informer_ids:(ALL наш_информер) 
	 * +abcde 
	 * +exactly_phrases:("abcde")
	 * +minus_words:(abcde)
	 * +type:teaser
	 * // +campaign_id:(все значения из списка кампаний)
	 * // -guid:(deprecatedOffers)
	 */
	string getOnPlacesString(const string& informerId)
	{
		if (informerId.empty())
		{
			return string();
		}
		string str = "+informer_ids:(all " + informerId + ") +abcde +exactly_phrases:(\"abcde\") +minus_words:(abcde) +type:teaser ";
		return str;
	}

	string getOnPlacesString1(const string& informerId, const string& topics, const string& query)
	{
		if (informerId.empty())
		{
			return string();
		}
		//string str = "+informer_ids:(all " + informerId + ") +abcde +exactly_phrases:(\"abcde\") +minus_words:(abcde) +type:teaser +topic_ids:(" + topics + ")";
		string str = "+informer_ids:(all " + informerId + ") +type:teaser +topic_ids:(" + topics + " common) ";
		if (!query.empty())
		{
			str = str+" -minus_words:(" + query + ") ";
		}

		return str;
	}


public:
	/**
	 * Обращение к индексу CLucene с коэффициентами в структуре Weights. Этот метод не производит непосредственное обращение, он только формирует необходимый запрос и отдаёт его на выполнению классу XXXSearcher.
	 * \param query - строка запроса, которую пользователь вбил в поисковике.
	 * \param userHistory - истории конкретного пользователя.
	 * \param context - контекст страницы.
	 * \param informerId - идентификатор информера, для которого модуль формирует ответ.
	 * \param campaigns - список кампаний, отобранных к просмотру.
	 * \param w - структура типа Weights, хранящая коэффициенты для каждого запроса. 
	 * 
	 * Возвращает список пар (идентификатор,вес).
	 * Идентификаторы - это идентификаторы РП, отобранных в результате обращения к индексу, веса - это веса, которые возвращает CLucene, умноженные на соответстующий коэффициент из структуры Weights, - веса соответствий РП запросу к индексу с учётом важности (приоритета) запроса.
	 * Возвращаемый список отсортирован по убыванию веса.
	 * 
	 * В методе выполняется 6 (реально - 5) запросов к индексу:
	 * 
	 * 1. запрос по "крутым" баннерам.
	 * +informer_ids:(ALL наш_информер) 
	 * +exactly_phrases:("abcde")
	 * +minus_words:(abcde)
	 * +type:banner
	 * +campaign_id:(все значения из списка кампаний)
	 * -guid:(deprecatedOffers)
	 * 
	 * 2. запрос по query - по строке запроса из поисковика.
	 * +(keywords:(query)
	 * exactly_phrases:("$query$"))
	 * -minus_words:(query)
	 * +campaign_id:(все значения из списка кампаний)
	 * -guid:(deprecatedOffers)
	 * 
	 * 3. РП по shortHistory - тот же запрос, что и в 2, только вместо query идёт КАЖДАЯ СТРОКА shortHistory.
	 * 
	 * 4. longHistory - только по keywords и minus_words.
	 * +keywords:(longHistory)
	 * -minus_words:(longHistory)
	 * +campaign_id:(все значения из списка кампаний)
	 * -guid:(deprecatedOffers)
	 * 
	 * 5. контекст. запроса нет, т.к. модуль в настоящее время не поддерживает контектс.
	 * 
	 * 6. РП на места.
	 * +informer_ids:(ALL наш_информер) 
	 * +exactly_phrases:("abcde")
	 * +minus_words:(abcde)
	 * +type:teaser
	 * +campaign_id:(все значения из списка кампаний)
	 * -guid:(deprecatedOffers)
	 * 
	 * Полученные списки (1 - 6) объединяются в один результирующий список. Результирующий список сортируется по убыванию рейтинга.
	 */
	list< pair<string, float>  > f1(const string& query, UserHistory& userHistory, const vector<string>& context, const string& informerId, const list<Campaign>& campaigns, const Weights &w)
	{
		
		//return list< pair<string, float>  >();

		//общие части всех запросов - список кампаний и начальное множество deprecatedOffers
		// +campaign_id:(все значения из списка кампаний)
		string strCamp = getCampaignsString(campaigns);
		// начальное множество deprecatedOffers - просто список идентификаторов, но в виде строки, чтоб не формировать при каждом запросе.
		
//LOG(INFO)<<"Depr size() = "<<userHistory.getDeprecatedOffers().size();
		
		string deprStr = listOfStringsToStringLimit(userHistory.getDeprecatedOffers());
		deprStr = constructFilter(deprStr);
//		LOG(INFO) << "COMMON FILTER: "<<deprStr;
		
		
		string topics =  listOfStringsToString(userHistory.getTopics());	//NEW!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!

		string str;

		//1. запрос по "крутым" баннерам.
		// +informer_ids:(ALL наш_информер) 
		// +exactly_phrases:("abcde")
		// +minus_words:(abcde)
		// +type:banner
		// +campaign_id:(все значения из списка кампаний)
		// -guid:(deprecatedOffers)
//		LOG (INFO) << "1. запрос по крутым баннерам\n";
		//string q = getPriorityBannersString(informerId);
		string q = getPriorityBannersString1(informerId, topics);				//NEW!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!

		list< pair<string, float>  > l1 = searcher->processWithFilter(constructQuery(q, strCamp, ""), deprStr, w.range_priority_banners, true);
//		LOG(INFO) << "l1.size()=" << l1.size() << "\n";

		////2. запрос по query - по строке запроса из поисковика.
		//// +(keywords:(query)
		//// exactly_phrases:("$query$"))
		//// -minus_words:(query)
		//// +campaign_id:(все значения из списка кампаний)
		//// -guid:(deprecatedOffers)
//		LOG (INFO) << "2. запрос по query"<<"   weight="<<w.range_query<<endl;
		q = getQueryString(query,informerId);
		list< pair<string, float>  > l2 = searcher->processWithFilter(constructQuery(q, strCamp, ""),deprStr, w.range_query, false);
//		LOG(INFO) << "l2.size()=" << l2.size() << "\n";

		////3. РП по shortHistory - тот же запрос, что и в 2, только вместо query идёт КАЖДАЯ СТРОКА shortHistory
//		LOG (INFO) << "3. запрос по shortHistory"<<"   weight="<<w.range_shot_term<<endl;
		//q = getQueryString( listOfStringsToString(userHistory.getShortHistory()) , informerId);
		//
		////str = listOfStringsToString(l2);
		list< pair<string, float>  > l3;
		list<pair<string, float> > l;
		list<string>::const_iterator i;
		for (i=userHistory.getShortHistory().begin(); i!=userHistory.getShortHistory().end(); i++)
		{
			q = getQueryString1(*i,informerId, query);
			//if(!str.empty())
			//	deprStr += (" " + str);//deprecatedOffers результат2
			l = searcher->processWithFilter(constructQuery(q, strCamp, ""),deprStr, w.range_shot_term, false);
			//LOG(INFO) << "l.size()=" << l.size() << "\n";
			l3.insert(l3.end(), l.begin(), l.end());
			//str = listOfStringsToString(l);//занесли в str (добавится на след. итерации к deprecated) идентификаторы полученных РП по текущей строке из shortHistory
		}
//		LOG(INFO) << "l3.size()=" << l3.size() << "\n";

		//
		////4. longHistory - только по keywords и minus_words.
		//// +keywords:(longHistory)
		//// -minus_words:(longHistory)
		//// +campaign_id:(все значения из списка кампаний)
		//// -guid:(deprecatedOffers)
//		LOG (INFO) << "4. запрос по longHistory"<<"   weight="<<w.range_long_term<<endl;
		q = getLongHistoryString(userHistory.getLongHistory());
		////str = listOfStringsToString(l3);
		////if(!str.empty())
		////	deprStr += (" " + str);//deprecatedOffers результат2 результат3
		list< pair<string, float>  > l4 = searcher->processWithFilter(constructQuery(q, strCamp, ""),deprStr, w.range_long_term, false);
//		LOG(INFO) << "l4.size()=" << l4.size() << "\n";
		//
		////5. контекст. не трогаю.
		//
		////6. РП на места.
		//// +informer_ids:(ALL наш_информер) 
		//// +exactly_phrases:("abcde")
		//// +minus_words:(abcde)
		//// +type:teaser
		//// +campaign_id:(все значения из списка кампаний)
		//// -guid:(deprecatedOffers)
//		LOG (INFO) << "6. запрос по местам\n";
		//q = getOnPlacesString(informerId);
		q = getOnPlacesString1(informerId, topics, query);						//NEW!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!	

		////str = listOfStringsToString(l4);
		////if(!str.empty())
		////	deprStr += (" " + str);//deprecatedOffers результат1 результат2 результат3 результат4
		list< pair<string, float>  > l6 = searcher->processWithFilter(constructQuery(q, strCamp, ""), deprStr,w.range_on_places,true);
		//list< pair<string, float>  > l6 = searcher->process1(constructQuery(q, strCamp, deprStr), w.range_on_places,true);

		//LOG(INFO) << "query -> "<<q;
		//LOG(INFO) << "depr  -> "<<deprStr;
		//LOG(INFO) << "camp -> "<<strCamp;
//		LOG(INFO) << "l6.size()=" << l6.size() << "\n";

		//теперь всё сливаем в результирующий список/вектор
		list< pair<string, float>  > result;

		//uint64_t strr = Misc::currentTimeMillis();


		result.insert(result.end(), l1.begin(), l1.end());
		result.insert(result.end(), l2.begin(), l2.end());
		result.insert(result.end(), l3.begin(), l3.end());
		result.insert(result.end(), l4.begin(), l4.end());
		result.insert(result.end(), l6.begin(), l6.end());

		//LOG(INFO) << "result.size()=" << result.size() << "\n";

		//сортируем по score
		result.sort(inverseOrderPairCompare);

		//LOG(INFO) << "result.size()=" << result.size() << "\n";
		

		//uint32_t srch = (int32_t)(Misc::currentTimeMillis() - strr);
		//LOG(INFO) << "\nLIST INSERTING AND UPDATING took: " << srch << " ms.\n"; 
		return result;
	}


	//==============================
	//RATING NEW!!!!!!!!!!!!
	//==============================
	map< string, float  > ratingSearch(const string& informerId, const list< pair<string, float>>& offerIds)
	{
		//LOG(INFO) << "Searching ratings for informers starts....: ";

		if (offerIds.empty()) return map< string, float  >();
		//string queryString =  "+offer:("+listOfStringsToString(offerIds)+") +informer:("+informerId+") ";
		//string queryString =  "+informer:("+informerId+") ";
		string queryString =  listOfStringsToString(offerIds)+" +informer:("+informerId+") ";

		queryString.push_back(0);
		//LOG(INFO) << "query for rating: "<<queryString;
		map< string, float  > result = searcher->process2(queryString);
		return result;

	}


	list< pair<string, float>  > f2(const string& query, UserHistory& userHistory, const vector<string>& context, const string& informerId, const list<Campaign>& campaigns, const Weights &w)
	{
		list< pair<string, float>  > result;
		list< pair<string, float>  > l;
		list<Campaign> curCampaign;
		list<Campaign>::const_iterator iter;

		for (iter=campaigns.begin(); iter!=campaigns.end(); iter++)
		{
			curCampaign.clear();
			curCampaign.push_back(*iter);
			l = f1(query, userHistory, context, informerId, curCampaign, w);
			result.insert(result.end(), l.begin(), l.end());
		}

		return result;
	}
};
