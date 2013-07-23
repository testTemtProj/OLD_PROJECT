/*
 *добавлено RealInvest Soft
 */
#pragma once
#include<string>
#include<list>
#include<vector>
#include <CLucene.h>
#include <CLucene/util/Misc.h>
#include <CLucene/config/repl_wchar.h>
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
	XXXSearcher(const string& directoryName);
	~XXXSearcher();
	
	/** \brief Метод обработки запроса к индексу.
	 *
	 * \param query - строка запроса
	 * \param weight - вес, на который домножаются весовые коэффициенты, получаемые от CLucene.
	 * @return список пар <идентификатор,вес>, где идентификатор - это идентификатор РП, удовлетворяющего запросу query, вес - значение, полученное путём умножения веса, возвращаемого CLucene на вес weight.
	 */
	list< pair<string, float> > process1(const string& query, float weight=1.0);


	/** \brief Массив стоп-слов.
	 * 
	 * Задаётся из кода.
	 */
	static const TCHAR* stop_words[];
protected:
	string directoryName;///< имя папки, в которой хранится индекс.

private:

};