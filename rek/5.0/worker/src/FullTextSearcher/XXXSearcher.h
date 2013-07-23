/*
 *добавлено RealInvest Soft
 */
#pragma once
#include<string>
#include<list>
#include<vector>
#include <stdlib.h>
#include <CLucene.h>
#include <CLucene/util/Misc.h>
#include <CLucene/config/repl_wchar.h>
#include <CLucene/search/QueryFilter.h>
#include "CLucene/snowball/SnowballAnalyzer.h"

//#include <boost/date_time/posix_time/ptime.hpp>//добавлено для замера времени.

#include <glog/logging.h>

using namespace std;
using namespace lucene::analysis;
using namespace lucene::index;
using namespace lucene::document;
using namespace lucene::queryParser;
using namespace lucene::search;
using namespace lucene::store;
using namespace lucene::util;

//using namespace boost::posix_time;//добавлено для замера времени.

/** \brief Класс, обрабатывающий запросы к индексу CLucene. */
class XXXSearcher
{
public:
	XXXSearcher(const string& dirNameOffer, const string& dirNameInformer);
	~XXXSearcher();
	
	void setLuceneIndexParams(string &folder_offer, string &folder_informer);


	/** \brief Метод обработки запроса к индексу.
	 *
	 * \param query - строка запроса
	 * \param weight - вес, на который домножаются весовые коэффициенты, получаемые от CLucene.
	 * @return список пар <идентификатор,вес>, где идентификатор - это идентификатор РП, удовлетворяющего запросу query, вес - значение, полученное путём умножения веса, возвращаемого CLucene на вес weight.
	 */
    list< pair < pair<string, float>, pair<string, string> > > processWithFilter(const string& query, const string& filter, float weight/* =1.0 */, bool onPlace, const string& branch, const string& conformity);

	map< string, float > process2(const string& query);
protected:
	string directoryName;///< имя папки, в которой хранится индекс.
	string index_folder_offer_;
	string index_folder_informer_;

private:

};
