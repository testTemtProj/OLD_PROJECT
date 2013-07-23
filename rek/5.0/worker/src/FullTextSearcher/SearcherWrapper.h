#pragma once
#include <string>
#include <vector>
#include <list>
#include <algorithm>
#include "XXXSearcher.h"
#include "../Campaign.h"
#include "../UserHistory.h"
#include <boost/algorithm/string.hpp>
#include <boost/algorithm/string/split.hpp>
#include <glog/logging.h>
#include <boost/regex.hpp>
#include <boost/regex/icu.hpp>


using namespace std;
using namespace boost::algorithm;

/** \brief Функция, сравнивающая пары a и b по возрастанию веса. Возвращает a.second < b.second. */
bool rigthOrderPairCompare(const pair< pair<string, float>, pair<string, string> >  &a, const pair< pair<string, float>, pair<string, string> >  &b);
/** \brief Функция, сравнивающая пары a и b по убыванию веса. Возвращает a.second > b.second. */
bool inverseOrderPairCompare(const pair< pair<string, float>, pair<string, string> >  &a, const pair< pair<string, float>, pair<string, string> >  &b);

/** \brief Структура, хранящая веса для всех шести запросов к lucene */
struct Weights{
public:
	float range_priority_banners;///< запрос 1 по "крутым" баннерам
	float range_query;///< запрос 2 по query
	float range_context;///< запрос 3 по контексту страницы
	float range_shot_term;///< запрос 4 по shortHistory
	float range_context_term;///< запрос 5 по контексту страницы
	float range_long_term;///< запрос 6 по longHistory
	float range_on_places;///< запрос 7 - РП по размещению

	Weights(){
		range_priority_banners = 1.0;
		range_query = 1.0;
		range_shot_term = 1.0;
		range_long_term = 1.0;
		range_context = 1.0;
		range_context_term = 1.0;
		range_on_places = 1.0;
	}
};

/** \brief Класс-обёртка работы с CLucene. 
 * Построение индекса производится вне модуля. Модуль лишь читает индекс.
 * Индекс располагается на жёстком диске.
 * Индекс хранит документы. В качестве документов выступают рекламные предложения из основной базы данных,
 * с которой работает модуль. В индекс занесены (проиндексированы) следующие поля:
 * \code
 * guid - идентификатор РП.
 * keywords - ключевые слова, закреплённые за РП.
 * minus_words - минус-слова, закреплённые за РП.
 * informer_ids - идентификатор информера, за которым закреплено РП.
 * campaign_id - идентификатор кампании, к которой принадлежит данное РП.
 * type - тип РП.
 * \endcode
 * 
 * Обращаясь на определённом языке запросов к индексу с помощью инструментов CLucene можно извлечь документы, удовлетворяющие условиям запроса.
 * Перевод нужных запросов на язык Lucene - это и есть предназначение этого класса.
 * 
 * Запросов к индексу всего 7 (реально 9 изза того что каждая строка долгосрочной, краткосрочной и контекстной истории это отдельный запрос).
 * \see Методы f1
 * 
 * Запросы к индексу:\n
 * 1)запрос по "крутым" баннерам: выбор РП типа баннер, которые по настройкам должны показываться или на всех информерах,
 * или на информере, для которого модуль обрабатывает запрос. 
 * Кроме того, выбираемые РП должны принадлежать к выбранным для показа рекламным кампаниям и не должны принадлежать ко 
 * множеству предложений, не подлежащих отбору.
 * 2)запрос по строке запроса из поисковика (если пользователь перешёл на сайт партнёрской сети из поисковика): выбор РП, у которых в ключевых словах 
 * и/или точных фразах встречается содержимое строки запроса, а в минус-словах его нет. Кроме того, выбираемые РП должны принадлежать 
 * к выбранным для показа рекламным кампаниям и не должны принадлежать ко множеству предложений, не подлежащих отбору. Рекламные компании для показа
 * выбираються без учета привязки к РБ, тоесть только по гео и временному таргетингу.
 * 3)запрос по контексту страницы, работает аналогично пункту 2 только в качестве содержимого строки запроса используються слова контекста передаваемые 
 * модулю в качестве входных параметров JavaScript загрузчиком отстраиваюшим Iframe.
 * 4)запрос по краткосрочной истории пользователя. Краткосрочная история - предыдущие 2 строки запроса из поисковика точно такие же запросы,
 * как в запросе 2, но для каждой строки запроса из истории. Т.е. в 2 выполняется один запрос, а в 3 - несколько (не более 2-х) таких же запросов 
 * с точностью до содержимого строки. Результаты объединяются в один.
 * 5)запрос по истории контекста страницы пользователя. История контекста страницы - предыдущие 2 строки запроса передаваемые модулю в качестве входных
 * параметров JavaScript загрузчиком отстраиваюшим Iframe, точно такие же запросы как в запросе 3, но для каждой строки запроса из истории.
 * Т.е. в 3 выполняется один запрос, а в 5 - несколько (не более 2-х) таких же запросов с точностью до содержимого строки.
 * Результаты объединяются в один.
 * 6)запрос по долгосрочной истории пользователя longHistory. Долгосрочная история пользователя - это строки заполняемые внешним сервисом. Обработка их
 * аналогична пунктам 4 и 5.
 * 7)запрос РП на места размещения: выбор РП типа тизер, которые по настройкам должны показываться или на всех информерах,
 * или на информере, для которого модуль обрабатывает запрос. Кроме того, выбираемые РП должны принадлежать к выбранным для показа рекламным
 * кампаниям и не должны принадлежать ко множеству предложений, не подлежащих отбору. Рекламные компании для показа рекламы выбираються с учетом привязки
 * компании к РБ
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
		searcher = new XXXSearcher(dirNameOffer, dirNameInformer);
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
	 *Конструирует запрос к индексу.

	 *@param qpart -  Сама суть запроса, без обязательных условий на отобранные кампании и предложения, не подлежащие отбору из индекса.
	 *@param campaingsString -  Список отобранных кампаний. РП должны отбираться только из этих кампаний.
	 *
	 *Примечания: campaingsString идёт уже в "готовом" виде, т.е. \code +campaign_id:(кампания1 кампания2 кампания3) \endcode
     */
	string constructQuery(const string &qpart, const string &campaingsString)
	{
		//VLOG(2) << "|" << qpart << "|" << campaingsString;
		//VLOG(2) << "|" << qpart.length() << "|" << campaingsString.length();
		if(qpart.empty() )
		{
			//VLOG(2) << "нет данных для запроса";
			return string();
		}
		string qstr = campaingsString + " "+qpart;
		qstr.push_back(0);
		//VLOG(2) << "запрос = " << "|" << qstr;
		return qstr;
	}

	string constructFilter(const string &deprecatedString)
	{
		string qstr = "+type:(teaser banner) ";
		if(deprecatedString.empty() )
		{
			//LOG(INFO)<<"deprecated history empty";
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
	string listOfStringsToString(const list< pair< pair<string, float>, pair<string, string> > >& l)
	{
		string str;
		list< pair< pair<string, float>, pair<string, string> > >::const_iterator p;
		for (p=l.begin(); p!=l.end(); p++)
		{
			if (!p->first.first.empty())
			{
				str += (p->first.first + " ");
			}
		}
		
		return str;
	}

    /**
        \brief Нормализирует строку строку.

    */
    string stringWrapper(const string &str, bool replaceNumbers = false)
    {   
        boost::u32regex replaceSymbol = boost::make_u32regex("[^а-яА-Яa-zA-Z0-9-]");
        boost::u32regex replaceExtraSpace = boost::make_u32regex("\\s+");
        boost::u32regex replaceNumber = boost::make_u32regex("(\\b)\\d+(\\b)");
        string t = str;
        //Заменяю все не буквы, не цифры, не минус на пробел
        t = boost::u32regex_replace(t,replaceSymbol," ");
        if (replaceNumbers)
        {
            //Заменяю отдельностояшие цифры на пробел, тоесть "у 32 п" замениться на
            //"у    п", а "АТ-23" останеться как "АТ-23"
            t = boost::u32regex_replace(t,replaceNumber," ");
        }
        //Заменяю дублируюшие пробелы на один пробел
        t = boost::u32regex_replace(t,replaceExtraSpace," ");
        boost::trim(t);
        return t;
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
	 return "+campaign_id:(6aa5383e-5ddb-4eb5-b693-d96acd17409b 6fcec5d5-3976-4ae0-a0dd-11056762af80 bd15f42a-643b-4d64-b24b-9b14d6b02095)";
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
	}

	/**
	 * Конструктор запроса для выбора РП по "крутым" баннерам.
	 * +informer_ids:(ALL наш_информер) 
	 * +abcde 
	 * +exactly_phrases:("abcde")
	 * +minus_words:(abcde)
	 * +type:banner
     */

	string getPriorityBannersString(const string& informerId)
	{
		if (informerId.empty())
		{
			return string();
		}
		//string str = "+informer_ids:(all OR " + informerId + ") +abcde +exactly_phrases:(\"abcde\") +minus_words:(abcde) +type:banner ";
		string str = "+informer_ids:(all OR " + informerId + ") +type:banner ";
		return str;
	}

	

	/**
	 * Конструктор запроса для выбора РП по ключевым словам
     * из поисковика, контекста страницы, истории краткосрочной, истории контекста, истории долгосрочной
	 * +(keywords:(query)
	 * exactly_phrases:("$query$"))
	 * -minus_words:(query)
	 */
	string getQueryString(const string& query)
	{
        string qsn = stringWrapper(query, true);
        string qs = stringWrapper(query);
		if (qsn.empty())
		{
			return string();
		}
        LOG(INFO) <<qsn;
        LOG(INFO) <<qs;
		string str = "+(keywords:(" + qsn + ") exactly_phrases:(" + ch + exCh + qs + exCh + ch + ")) -minus_words:(" + qsn + ") ";
		return str;
	}

	/**
	 * Конструктор запроса для выбора РП на места.
	 * +informer_ids:(ALL наш_информер) 
	 * +type:teaser
	*/
	string getOnPlacesString(const string& informerId)
	{
		if (informerId.empty())
		{
			return string();
		}
		string str = "+informer_ids:(all " + informerId + ") +type:teaser";
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
	 * \param campaignsAllGeo - список кампаний, отобранных к просмотру без учёта привязки к РБ.
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
	list< pair< pair<string, float>, pair<string, string> > > f1(const string& query, UserHistory& userHistory, const string& context, const string& informerId, const list<Campaign>& campaigns, const list<Campaign>& campaignsAllGeo, const Weights &w)
	{
		//общие части всех запросов - список кампаний и начальное множество deprecatedOffers

		// +campaign_id:(все значения из списка кампаний выбраных для показа с учетом привязки к РБ и гео-временных таргетинговых настроек)
		string strCamp = getCampaignsString(campaigns);

		// +campaign_id:(все значения из списка кампаний выбраных для показа с без учета привязки к РБ но с учетом
        // гео-временных таргетинговых настроек)
        //string strCampAllGeo = getCampaignsString(campaignsAllGeo);
        string strCampAllGeo = getCampaignsString(campaignsAllGeo);

		//начальное множество deprecatedOffers - просто список идентификаторов РП неподлежаших к показу,
        //но в виде строки, чтоб не формировать при каждом запросе.
		string deprStr;
        deprStr = listOfStringsToString(userHistory.getDeprecatedOffers());
		deprStr = constructFilter(deprStr);

		////1. запрос по "крутым" баннерам.
		//
		//
		////
		LOG(INFO) << "Запрос по крутым баннерам";
		string q = getPriorityBannersString(informerId);
		list< pair< pair<string, float>, pair<string, string> > > l1; 
        l1 = searcher->processWithFilter(constructQuery(q, strCamp), deprStr, w.range_priority_banners, true, "L1", "conform");
		LOG(INFO) << "Выбрано РП" << l1.size();

		////2. запрос по query - по строке запроса из поисковика.
		//
		//
		////
        list< pair< pair<string, float>, pair<string, string> > > l2;
        string strSS = query;
        trim(strSS);
    	if (!strSS.empty())
	    {
            LOG(INFO) << "Запрос по П/З query = " << strSS;
            q = getQueryString(strSS);
            l2 = searcher->processWithFilter(constructQuery(q, strCamp),deprStr, w.range_query, false, "L2", "conform");
            LOG(INFO) << "Выбрано РП" << l2.size();
        }

        ////3. запрос по context - по контексту страницы.
        //
        //
        ////
        list< pair< pair<string, float>, pair<string, string> > > l3;
        string strCS = context;
        trim(strCS);
    	if (!strCS.empty())
	    {
            LOG(INFO) << "Запрос по контексту страницы context = " << strCS;
            q = getQueryString(strCS);
            l3 = searcher->processWithFilter(constructQuery(q, strCamp),deprStr, w.range_context, false, "L3", "conform");
            LOG(INFO) << "Выбрано РП" << l3.size();
        }
		////4. РП по shortHistory - тот же запрос, что и в 2, только вместо query идёт КАЖДАЯ СТРОКА shortHistory
		//
		//
		////
		list< pair< pair<string, float>, pair<string, string> > > l4;
		list< pair< pair<string, float>, pair<string, string> > > ls;
		list<string>::const_iterator i;
		for (i=userHistory.getShortHistory().begin(); i!=userHistory.getShortHistory().end(); i++)
		{
            string strSH = *i;
            trim(strSH);
    		if (!strSH.empty())
	    	{
                LOG(INFO) << "Запрос по К.И query = " << strSH;
                q = getQueryString(strSH);
                ls = searcher->processWithFilter(constructQuery(q, strCamp),deprStr, w.range_shot_term, false, "L4", "conform");
                LOG(INFO) << "Выбрано РП" << ls.size();
                l4.insert(l4.end(), ls.begin(), ls.end());
            }
		}
		////5. РП по contextHistory - тот же запрос, что и в 3, только вместо query идёт КАЖДАЯ СТРОКА contextHistory
		//
		//
		////
		list< pair< pair<string, float>, pair<string, string> > > l5;
		list< pair< pair<string, float>, pair<string, string> > > lc;
		list<string>::const_iterator itrc;
		for (itrc=userHistory.getContextHistory().begin(); itrc!=userHistory.getContextHistory().end(); itrc++)
		{
            string strCH = *itrc;
            trim(strCH);
    		if (!strCH.empty())
	    	{
                LOG(INFO) << "Запрос по Контекст Истории = " << strCH;
                q = getQueryString(strCH);
                lc = searcher->processWithFilter(constructQuery(q, strCamp),deprStr, w.range_shot_term, false, "L5", "conform");
                LOG(INFO) << "Выбрано РП" << lc.size();
                l5.insert(l5.end(), lc.begin(), lc.end());
            }
		}

		////6. РП по longHistory - что и в 2, только вместо query идёт КАЖДАЯ СТРОКА longHistory
		//
		//
		////
        list< pair< pair<string, float>, pair<string, string> > > l6;
        list< pair< pair<string, float>, pair<string, string> > > lh;
        list<string>::const_iterator itr;
        for (itr=userHistory.getLongHistory().begin(); itr!=userHistory.getLongHistory().end(); itr++)
        {
            string strLH = *itr;
            trim(strLH);
    		if (!strLH.empty())
	    	{
                LOG(INFO) << "Запрос по Д.И = " << strLH;
                q = getQueryString(strLH);
                lh = searcher->processWithFilter(constructQuery(q, strCamp),deprStr, w.range_long_term, false, "L6", "conform");
                LOG(INFO) << "Выбрано РП" << lh.size();
                l6.insert(l6.end(), lh.begin(), lh.end());
            }
        }
		////7. РП на места.
		//
		//
		////
		LOG(INFO) << "Запрос по местам";
		q = getOnPlacesString(informerId);	
		list< pair< pair<string, float>, pair<string, string> > > l7;
        l7 = searcher->processWithFilter(constructQuery(q, strCamp), deprStr,w.range_on_places,true, "L7", "conform");
		LOG(INFO) << "Выбрано РП " << l7.size();

		//теперь всё сливаем в результирующий список/вектор
		list<pair<pair<string, float>, pair<string, string>>> result;

		//uint64_t strr = Misc::currentTimeMillis();
		result.insert(result.end(), l1.begin(), l1.end());
		result.insert(result.end(), l2.begin(), l2.end());
		result.insert(result.end(), l3.begin(), l3.end());
		result.insert(result.end(), l4.begin(), l4.end());
		result.insert(result.end(), l5.begin(), l5.end());
		result.insert(result.end(), l6.begin(), l6.end());
		result.insert(result.end(), l7.begin(), l7.end());

		LOG(INFO) << "Всего выбрано РП " << result.size();

		//сортируем по score
		result.sort(inverseOrderPairCompare);

		//uint32_t srch = (int32_t)(Misc::currentTimeMillis() - strr);
		//VLOG(1) << "Вставка в результируюший список заняла: " << srch << " мс";
		return result;
	}


	//==============================
	//Запрос на получение рейтингов РП из индекса
    //выполняеться только если передаваемый в него список гюидов РП не пустой.
	//==============================
	map< string, float  > ratingSearch(const string& informerId, const list<pair<pair<string, float>, pair<string, string>>>& offerIds)
	{
		//VLOG(1) << "Поиск рейтингов РП для РБ";
		if (offerIds.empty()) return map< string, float  >();
		string queryString =  "+offer:("+listOfStringsToString(offerIds)+") +informer:("+informerId+")";
		queryString.push_back(0);
		//VLOG(2) << "Запрос для выбора рейтингов РП для РБ: "<<queryString;
		map< string, float  > result = searcher->process2(queryString);
		return result;

	}

};
