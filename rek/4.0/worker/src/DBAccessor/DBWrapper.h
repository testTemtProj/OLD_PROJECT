/**
 * Добавлено RealInvest Soft
 */
#ifndef DBWrapper_H
#define DBWrapper_H

#include "redisclient.h"
#include "DBConnectionParams.h"
#include "../UserHistory.h"
#include "../Offer.h"

#include <iostream>
#include <fstream>
#include <cstring>
#include <boost/date_time.hpp>
#include <boost/date_time/gregorian/gregorian.hpp>


#include <glog/logging.h>


using namespace std;
using namespace boost::posix_time;
using namespace boost::gregorian;


namespace redisDB {
/** \brief
 
    Класс, обеспечивающий взаимодействие с базами данных Redis.

    Класс обеспечивает доступ к четырем базам данных: </BR>
	- база данных краткосрочной истории пользователя</BR>
	- база данных долгосрочной истории пользователя</BR>
	- база данных истории показов пользователя</BR>
	- база данных контекста страниц</BR>
	
	Все базы имеют одинаковую структуру. Ключом выступает ip-адрес пользователя. 
	В качестве значения ключа используется SortedSet. В базах данных долгосрочной 
	истории и истории показов также хранятся ключи вида ip_, которые в качестве 
	веса берут величину, привязанную к дате последнего обновления значения.
	
	Значение score вычисляется по следующей формуле:
	\code
	
		score = (second_clock::local_time() - d(1970,Jan,1)) / 1000000;
	
    \endcode	
	
	База данных краткосрочной истории содержит к качестве значения ключа строку запроса, заданную
	пользователем в поисковике. Предполагается что для каждого ключа хранится не более двух 
	предудыщих запросов.
	
	Например:
	\code
    // Добавление в иcторию пользователя с ip = 192.168.1.1.04 значения строки с поисковика 
	// query="Nokia phone". 
	// В качестве веса берется величина, вычисленная по дате последнего обновления значения
	ZADD 192.168.1.1.104 123123123 "Nokia phone"
    \endcode
		
	База данных долгосрочной истории содержит к качестве значения ключа ключевые слова, 
	соответствующие рекламному предложению, по которому пользователь выполнил переход.
	Модуль GR-M не отвечает за заполнение данной базы, а использует ее только для чтения.
	Предполагается, что база заполнена следуюшим образом:
	
	Пример:

	\code
    // Добавление в долгосрочную иcторию пользователя с ip = 192.168.1.1.04 информации о выборе  
	// рекламного предложения имеющего ключевые слова "Nokia" и "дорогой телефон"
	
	ZADD 192.168.1.1.104  3  "Nokia"					//если ключевое слово встречалось ранее, то его вес увеличивается на единицу
	ZADD 192.168.1.1.104  1  "дорогой телефон"			//если ранее это слово не встречалось, то score=1
	ZADD 192.168.1.1.104_  5235412412312  "Nokia"   // информация о последнем обновлении
	ZADD 192.168.1.1.104_  5235412412312  "дорогой телефон"   // информация о последнем обновлении
    \endcode
	
	База данных истории показов пользователя хранит информацию о количестве доступных показов
	рекламных предложений, которые имеют ограничения на показ.
	
	Например:
	\code
    // Добавление в иcторию пользователя с ip = 192.168.1.1.04 информации о том, что  
	// рекламное предложение  "guid": "464fa8fd-1d3c-43e4-80e7-e2c38a911b6c" может быть
	// может быть показано пользователю еще 2 раза
	
	ZADD 192.168.1.1.104  2  "464fa8fd-1d3c-43e4-80e7-e2c38a911b6c"					//доступное количество показов
	ZADD 192.168.1.1.104_  5235412412312  "464fa8fd-1d3c-43e4-80e7-e2c38a911b6c"   // информация о последнем обновлении
    \endcode
	
	В данной версии модуля работа с базой данных контекста страницы не ведется.

 */
class DBWrapper
{
private:
	///redis-client для работы с краткосрочной историей
	boost::shared_ptr<redis::client> shortterm;		
	
	///redis-client для работы с долгосрочной историей
	boost::shared_ptr<redis::client> longterm;		
	
	///redis-client для работы с историей показов
	boost::shared_ptr<redis::client> views;			
	
	///redis-client для работы с контекстом страницы
	boost::shared_ptr<redis::client> pagekeywords;	
	

	///время жизни ключей в базе данных краткосрочной истории
	int shortterm_expire;	

	///время жизни ключей в базе данных долгосрочной истории
	int views_expire;	

	DBConnectionParams params_;	 

	static const int VIEWS_LIMIT = 50;
              
public:


    DBWrapper()
    {

    }

    ~DBWrapper()
    {

    }
    
     
	/** \brief  Обновление истории показов пользователя

        \param ip        идентификатор пользователя
	    \param result    вектор выбранных к показу рекламных предложений
		
		Если выбранное к показу рекламное предложение имеет ограничение на количество показов конкретному пользователю,
		то соответствующее рекламное предложение заносится в базу данных истории показов пользователя.
		
		Если данное рекламное предложение показано пользователю впервые, то оно заносится в базу 
		с весом на единицу меньшим, чем возможное количество показов. 
		Например, если рекламное предложение "guid": "464fa8fd-1d3c-43e4-80e7-e2c38a911b6c" может быть показано конкретному
		пользователю не более двух раз, то при первом просмотре данного рекламного предложения 
		в базу занесется следующее значение:

		\code
		ZADD 192.168.1.1.104  1  "464fa8fd-1d3c-43e4-80e7-e2c38a911b6c"					
		\endcode	

		Если выбранное к показу рекламное предложение показывается пользователю не в первые,
		то вес рекламного предложения уменьшается на единицу. Например, при повторном показе 
		рекламного предложения "guid": "464fa8fd-1d3c-43e4-80e7-e2c38a911b6c" история пользователя будет обновлена следующим образом:
		\code
		ZINCRBY 192.168.1.1.104  -1  "464fa8fd-1d3c-43e4-80e7-e2c38a911b6c"					
		\endcode

		Поскольку согласно алгоритму отбора рекламных предложений пользователю не могут быть 
		показаны предложения, исчерпавшие свой лимит показа, то в БД истории показов вес рекламных предложений не можут становится
		отрицательным.
		
		Параллельно с ключом ip обновляется и ключ ip_, который в качестве 
		веса берет величину, привязанную к дате последнего обновления значения.
	
		Значение score вычисляется по следующей формуле:
		\code
		
			score = (second_clock::local_time() - d(1970,Jan,1)) / 1000000;
		
		\endcode	
		
		Рекламные предложение, не имеющие ограничения на количества показов, в базе данных истории показов пользователя
		не регистрируются.
		
		При создании ключа для конкретного пользователя ему выставляется время жизни, которое задается параметром views_expire.
     */
    void updateDeprecatedUserHistory(const std::string & ip, const vector<Offer> &result)
    {

		try{
		if (!getViewHistoryStatus()) 
			views = init_non_cluster_clientt(params_.redis_user_view_history_host_, params_.redis_user_view_history_port_);
		}catch (redis::redis_error & e) 
  		{
				LOG(ERROR) << "Redis client does NOT reconnect! Probably redis-server for views history is failed!";
				return;
		}

		redis::client & db_views = *views;

		try{
			

			//LOG(INFO) << "updateDeprecatedUserHistory start\n";
			//LOG(INFO) << "ip = " << ip << "\n";
			//LOG(INFO) << "result.size() = " << result.size() << "\n";

			std::string ip_ = ip;
			ip_.append("_");
			//LOG(INFO) << " before while" << "\n";

			vector<Offer>::const_iterator p = result.begin();
			while (p != result.end())
			{
				//LOG(INFO) << "----------------------------------------------------------------------\n";
				//LOG(INFO) << " p->uniqueHits() = " <<p->uniqueHits()<< "   guid = " <<p->id()<<"\n";

				if (p->uniqueHits()!=-1)
				{
					if (db_views.exists(ip))
					{
						//LOG(INFO) << " This key exists ....\n";
						long int k = -1;
						try{
						 k =  db_views.zrank(ip,p->id());}catch (redis::redis_error & e){/*LOG(INFO) << "added value not in history\n";*/}

						if (k==-1)
						{
							

							try{ 
								//LOG(INFO) <<"Adding new value"<<endl;
								db_views.zadd(ip,(p->uniqueHits())-1,p->id());
								//LOG(INFO) <<"IP key updated...."<<endl;
								db_views.zadd(ip_,currentDateToInt(),p->id());
								//LOG(INFO) <<"IP_ key updated...."<<endl;
							} catch (redis::redis_error & e){
    								LOG(INFO) << "Redis exception: " << e.what() << endl;
  
  							}

						}
						else {
							//LOG(INFO) <<"Value is looked for.."<<endl;

							int temp = db_views.zscore(ip,p->id());
							//LOG(INFO) <<"found k ..."<<k<<"  zscore(ip,p->id())="<<temp<<endl;

							if (temp>0) 
							{
								db_views.zincrby(ip, p->id(), -1);
								//LOG(INFO) << ip_ <<"   "<<currentDateToInt()<<"   "<< p->id()<<"\n";
								try{
								db_views.zadd(ip_,currentDateToInt(),p->id());}catch (redis::redis_error & e){/*LOG(INFO) << "not add only updated\n";*/}
								//LOG(INFO) << " after zadd for ip_\n";
							}
							//else
								//LOG(INFO) << "Element has score = 0 \n";

						}
					}
					else
					{
						//LOG(INFO) << " This key not exists ....\n";

						db_views.zadd(ip,(p->uniqueHits())-1,p->id());
						db_views.zadd(ip_,currentDateToInt(),p->id());
						db_views.expire(ip, views_expire);
						db_views.expire(ip_, views_expire);
					}
				}
				p++;
			}

		cutDeprecatedUserHistory(ip);

		}catch (redis::redis_error & e) 
		{
			LOG(INFO) << "Redis updateDeprecatedUserHistory failed!";
		}
		catch (...) 
		{
			LOG(INFO) << "Redis updateDeprecatedUserHistory failed with lexical cast error!";
		}

		//LOG(INFO) << "updateDeprecatedUserHistory end\n";

    }
 	
   
	
	/** \brief  Обновление краткосрочной истории пользователя

        \param ip        идентификатор пользователя
	    \param query     строка запроса для добавления в историю
		
		При переходе на сайт партнерской сети с поисковика отбор рекламных предложений производится в 
		соответсвии с этим запросом. После этого сам запрос заносится в базу данных краткосрочной истории пользователя.
		
		Количество значений у ключей в данной базе не может привышать двух, таким образом в поиске по краткосрочной
		истории участвует не более двух последних запросов.
		
		Например:
		\code
		// Добавление в иcторию пользователя с ip = 192.168.1.1.04 значения строки с поисковика 
		// query="Nokia phone". 
		// В качестве веса берется величина, вычисленная по дате последнего обновления значения
		ZADD 192.168.1.1.104 123123123 "Nokia phone"
		\endcode		
		
		При создании ключа для конкретного пользователя ему выставляется время жизни, которое задается параметром \see shortterm_expire.
     */
    void updateShortHistory(const std::string & ip, const std::string & query)
	{

		try{
		if (!getShortTermStatus()) 
			shortterm = init_non_cluster_clientt(params_.redis_short_term_history_host_, params_.redis_short_term_history_port_);
		}catch (redis::redis_error & e) 
  		{
				LOG(ERROR) << "Redis client does NOT reconnect! Probably redis-server for short history is failed!";
				return;
		}

		try{
			//LOG(INFO) << "updateShortHistory start\n";

			if (!query.empty())
			{
				redis::client & db_shortterm = *shortterm;

				//LOG(INFO) << ip<<"  "<<currentDateToInt()<<"  "<<query<<endl;

				try{
					db_shortterm.zadd(ip, currentDateToInt(), query); 
				}catch (redis::redis_error & e){
					//LOG(INFO) << "not add only updated\n";
				}

				db_shortterm.expire(ip, shortterm_expire);

				if (db_shortterm.zcount(ip, 0,INFINITY)>=3)
					db_shortterm.zremrangebyrank(ip, 0, 0);

			}
		}catch (redis::redis_error & e) 
  		{
    			LOG(ERROR) << "Redis updateShortHistory failed!";
  		}
		//LOG(INFO) << "updateShortHistory end\n";
    }
    

	
	/** \brief  Формирование объекта UserHistory по его идентификатору

        \param ip        идентификатор пользователя
		
		Объект UserHistory представляет собой совокупность историй конкретного пользователя: краткосрочной истории, 
		долгосрочной истории и истории показов.
		
		При формировании краткосрочной истории берутся все значения ключа из базы данных краткосрочной истории.
		
		При формировании долгосрочной истории берутся ПЯТЬ наибольших по весу ключевых фраз с помощью конструкции
		
		\code
		ZREVRANGEBYSCORE ip +inf 0 LIMIT 5
		\endcode	
		
		При формировании истории показов берутся те рекламные предложения, которые не могут быть показаны данному пользователю,
		т.е. такие рекламные предложения, чей вес равен 0.
		
		\code
		ZRANGEBYSCORE ip -1 0
		\endcode
		
			
	*/
    UserHistory * getUserHistoryById(const std::string & ip) 
    {



		//LOG(INFO) << "GetUserHistoryById : "<<ip<<endl;
        UserHistory * userHistory = new UserHistory (ip);
		try{
			redis::client::string_vector history;
			redis::client & db_shortterm= *shortterm;
			if (db_shortterm.exists(ip))
			{	
				db_shortterm.zrevrange(ip, 0, -1, history);
				//LOG(INFO) << "short history..."<<history.size();	
				for (unsigned int i=0; i<history.size();i++)
				{
					//LOG(INFO) << "      "<<history[i];
					userHistory->addShortHistory(history[i]);
				}
			}	

			redis::client & db_longterm= *longterm;
			redis::client::string_vector slivki;
			if (db_longterm.exists(ip))
			{
				db_longterm.zrevrangebyscore(ip, INFINITY, 0.0, slivki, 0,5);
				//LOG(INFO) << "long history..."<<slivki.size();
				for (unsigned int i=0; i<slivki.size();i++)
				{
					userHistory->addLongHistory(slivki[i]);
				} 
			}

			redis::client & db_views= *views;
			history.clear();
			if (db_views.exists(ip))
			{
				db_views.zrangebyscore(ip, -1.0, 0.0, history);
				//LOG(INFO) << "view history..."<<history.size();
				for (unsigned int i=0; i<history.size();i++)
				{
					userHistory->addDeprecatedOffer(history[i]);
				}
			}
		}catch (redis::redis_error & e) 
  		{
    			LOG(ERROR) << "Redis getUserHistoryById  failed!";
			try{
			if (!getViewHistoryStatus()) views = init_non_cluster_clientt(params_.redis_user_view_history_host_, params_.redis_user_view_history_port_);
			if (!getShortTermStatus()) shortterm = init_non_cluster_clientt(params_.redis_short_term_history_host_, params_.redis_short_term_history_port_);
			if (!getLongTermStatus()) longterm = init_non_cluster_clientt(params_.redis_long_term_history_host_, params_.redis_long_term_history_port_);
			init_non_cluster_clientt(params_.redis_page_keywords_host_, params_.redis_page_keywords_port_);
			LOG(ERROR) << "Redis client reconnect !";
			}catch (redis::redis_error & e) 
  			{
				LOG(ERROR) << "Redis client does NOT reconnect! Probably redis-server is failed!";

			}


 		}
		//LOG(INFO) << "GetUserHistoryById end.\n";             
        return userHistory;
    }

	/** \brief  Формирование объекта UserHistory по его идентификатору с усетом тематики страницы

        \param ip        идентификатор пользователя
		\param location        адрес страницы, на которой будет располагаться информер
		
		Объект UserHistory представляет собой совокупность историй конкретного пользователя: краткосрочной истории, 
		долгосрочной истории и истории показов.
		
		При формировании краткосрочной истории берутся все значения ключа из базы данных краткосрочной истории.
		
		При формировании долгосрочной истории берутся ПЯТЬ наибольших по весу ключевых фраз с помощью конструкции
		
		\code
		ZREVRANGEBYSCORE ip +inf 0 LIMIT 5
		\endcode	
		
		При формировании истории показов берутся те рекламные предложения, которые не могут быть показаны данному пользователю,
		т.е. такие рекламные предложения, чей вес равен 0.
		
		\code
		ZRANGEBYSCORE ip -1 0
		\endcode
		
			
	*/	
	UserHistory * getUserHistoryByIdAndLocation(const std::string & ip, const std::string & location1) 
    {

		string location = location1;

		//LOG(INFO) << "GetUserHistoryById : "<<ip<<endl;
        UserHistory * userHistory = new UserHistory (ip);
		try{
			redis::client::string_vector history;
			redis::client & db_shortterm= *shortterm;
			if (db_shortterm.exists(ip))
			{	
				db_shortterm.zrevrange(ip, 0, -1, history);
				//LOG(INFO) << "short history..."<<history.size();	
				for (unsigned int i=0; i<history.size();i++)
				{
					//LOG(INFO) << "      "<<history[i];
					userHistory->addShortHistory(history[i]);
				}
			}	

			redis::client & db_longterm= *longterm;
			redis::client::string_vector slivki;
			if (db_longterm.exists(ip))
			{
				db_longterm.zrevrangebyscore(ip, INFINITY, 0.0, slivki, 0,5);
				//LOG(INFO) << "long history..."<<slivki.size();
				for (unsigned int i=0; i<slivki.size();i++)
				{
					userHistory->addLongHistory(slivki[i]);
				} 
			}

			redis::client & db_views= *views;
			history.clear();
			if (db_views.exists(ip))
			{
				db_views.zrangebyscore(ip, -1.0, 0.0, history);
				//LOG(INFO) << "view history..."<<history.size();
				for (unsigned int i=0; i<history.size();i++)
				{
					userHistory->addDeprecatedOffer(history[i]);
				}
			}

			redis::client & db_topics= *pagekeywords;
    			redis::client::string_set members;
    			LOG(INFO)<<"param location = "<<location;
			while (!location.empty())
			{
				if (db_topics.exists(location))
				{
					LOG(INFO)<<"url " << location<<"  founded";

					db_topics.smembers(location, members);
					
  					set<string>::key_compare mycomp;
  					set<string>::iterator it;
  					string highest;

  					mycomp = members.key_comp();

					highest=*members.rbegin();
  					it=members.begin();
  					do {
						LOG(INFO)<<"     topics_ids: "<<*it;
    						userHistory->addTopic(*it);

  					} while ( mycomp(*it++,highest) );
					break;

				}
				else
				location = CutLocation(location);
				
				//LOG(INFO)<<"add to topics" << location;
				
				
			}
			if ((userHistory->getTopics()).empty()) userHistory->addTopic("common");


		}catch (redis::redis_error & e) 
  		{
    			LOG(ERROR) << "Redis getUserHistoryById  failed!";
			try{
			if (!getViewHistoryStatus()) views = init_non_cluster_clientt(params_.redis_user_view_history_host_, params_.redis_user_view_history_port_);
			if (!getShortTermStatus()) shortterm = init_non_cluster_clientt(params_.redis_short_term_history_host_, params_.redis_short_term_history_port_);
			if (!getLongTermStatus()) longterm = init_non_cluster_clientt(params_.redis_long_term_history_host_, params_.redis_long_term_history_port_);
			pagekeywords = init_non_cluster_clientt(params_.redis_page_keywords_host_, params_.redis_page_keywords_port_);
			LOG(ERROR) << "Redis client reconnect !";
			}catch (redis::redis_error & e) 
  			{
				LOG(ERROR) << "Redis client does NOT reconnect! Probably redis-server is failed!";

			}


 		}
		//LOG(INFO) << "GetUserHistoryById end.\n";             
        return userHistory;
    }

	
	
	/** \brief Получение контекста страницы по url */
    vector<std::string> getContextByUrl(const std::string & url) 
    {
		redis::client & db_pagekeywords= *pagekeywords;
		redis::client::string_vector history;
		vector<std::string> result;
		if (db_pagekeywords.exists(url))
		{
			db_pagekeywords.zrevrange(url, 0, -1, history);

			for (unsigned int i=0; i<history.size();i++)
			{	
				result.push_back(history[i]);
			}
		}
		return result;
    }

	/** \brief  Инициализацтя подключения к базам данных. Параметры подключения берутся из файла. 

        Метод используется для тестирования.
	*/	
	int InitDBs()
	{
		string::size_type posBeginIdx, posEndIdx;
		string::size_type ipos=0;
		string            dbType, temp, str, sValue, hostName, port;
		string            sKeyWord;
		const string      sDelim( ":" );

		
		std::ifstream input ("mu");
		if(input.fail())
		{
			LOG(INFO) << "файл mu не открыт.\n";
			return -1;
		}
		while(std::getline(input,str)){
		if( str.empty() );                     // Ignore empty lines
		else
		   {
			  posEndIdx = str.find_first_of( sDelim );
			  dbType  = str.substr( ipos, posEndIdx ); // Extract word
			  posBeginIdx = posEndIdx + 1;  // Beginning of next word (after ':')

			temp = str.substr(posBeginIdx, str.size());
			posEndIdx = temp.find_first_of( sDelim );
			hostName = temp.substr( ipos, posEndIdx ); // Extract word
			port = temp.substr(posEndIdx +1, temp.size());
			if (dbType.compare("ShortTermHistory")==0) shortterm = init_non_cluster_clientt(hostName, atoi(port.c_str()));
			if (dbType.compare("LongTermHistory")==0) longterm = init_non_cluster_clientt(hostName, atoi(port.c_str()));
			if (dbType.compare("UserViewsHistory")==0) views = init_non_cluster_clientt(hostName, atoi(port.c_str()));
			if (dbType.compare("PageKeywords")==0) pagekeywords = init_non_cluster_clientt(hostName, atoi(port.c_str()));


   		}
			LOG(INFO) <<dbType<<"  - "<<hostName<<" -  "<<port<<endl;
	}

	LOG(INFO) <<"After file"<<endl;
	input.close();
	LOG(INFO) <<"After input.close();"<<endl;
	return 0;
}

	/** \brief  Инициализация подключения к базам данных краткосрочной истории, долгосрочной истории и истории показов.

        \param param        параметры подключения
	*/
	int InitConnection(DBConnectionParams& param)
		{
			params_ = param;
			try{
				shortterm = init_non_cluster_clientt(param.redis_short_term_history_host_, param.redis_short_term_history_port_);
				longterm = init_non_cluster_clientt(param.redis_long_term_history_host_, param.redis_long_term_history_port_);
				views = init_non_cluster_clientt(param.redis_user_view_history_host_, param.redis_user_view_history_port_);
				pagekeywords = init_non_cluster_clientt(param.redis_page_keywords_host_, param.redis_page_keywords_port_);

				shortterm_expire = param.shortterm_expire_;
				views_expire = param.views_expire_;
			}catch (redis::redis_error & e) 
			{
					LOG(ERROR) << "Redis connection failed!";
				

					return -1;
			}
		return 1;
	}

	/** \brief  Статус подключения к базе данных краткосрочной истории.
	
		Возвращает 1 в случае, если подключение работает, и 0 в противном случае.
	*/
	int getShortTermStatus()
	{
		try{
			redis::client & db_shortterm= *shortterm;
			db_shortterm.exists("test");
			return 1;
		}catch (redis::redis_error & e) 
  		{
    			LOG(ERROR) << "Redis DB error. Short term DB is down.";
    			return 0;
  		}
	}

	/** \brief  Статус подключения к базе данных долгосрочной истории.

		Возвращает 1 в случае, если подключение работает, и 0 в противном случае.
	*/
	int getLongTermStatus()
	{
		try{
			redis::client & db_longterm= *longterm;
			db_longterm.exists("test");
			return 1;
		}catch (redis::redis_error & e) 
  		{
    			LOG(ERROR) << "Redis DB error. Long term DB is down.";
    			return 0;
  		}
	}

	/** \brief  Статус подключения к базе данных истории показов пользователя
	
		Возвращает 1 в случае, если подключение работает, и 0 в противном случае.
	*/
	int getViewHistoryStatus()
	{
		try{
			redis::client & db_views= *views;
			db_views.exists("test");
			return 1;
		}catch (redis::redis_error & e) 
  		{
    			LOG(ERROR) << "Redis DB error. View history DB is down.";
    			return 0;
  		}
	}




	/** \brief  Статус подключения к базе данных истории показов пользователя
	
		Возвращает 1 в случае, если подключение работает, и 0 в противном случае.
	*/
	int getPageKeywordsStatus()
	{
		try{
			redis::client & db_page= *pagekeywords;
			db_page.exists("test");
			return 1;
		}catch (redis::redis_error & e) 
  		{
    			LOG(ERROR) << "Redis DB error. Page keywords DB is down.";
    			return 0;
  		}
	}

	/** \brief  Создание redis-client с параметрами по умолчанию

	Значения по умолчанию: localhost:6379
	*/
	boost::shared_ptr<redis::client> init_non_cluster_clientt()
	{
	  const char* c_host = getenv("REDIS_HOST");
	  string host = "localhost";
	  if(c_host)
		host = c_host;
	cerr << "HOST" << "  " << host <<endl;

	  return boost::shared_ptr<redis::client>( new redis::client(host) );
	}

	/** \brief  Создание redis-client 

	    \param server_host        	адрес сервера
	    \param server_port     		порт сервера
	*/
	boost::shared_ptr<redis::client> init_non_cluster_clientt(const std::string &server_host, int server_port)
	{
	LOG(INFO) <<"==="<<"  - "<<server_host<<" -  "<<server_port<<endl;
		return boost::shared_ptr<redis::client>( new redis::client(server_host,server_port) );
	}




	/** \brief  Вычисление величины, привязанной к текущей дате.
	
	Значение score вычисляется по следующей формуле:
	\code
	
		score = (second_clock::local_time() - d(1970,Jan,1)) / 1000000;
	
    \endcode	
	
	Значение используется для выставления веса значений в базе данных краткосрочной истории и истории показов.
	*/
	boost::int64_t currentDateToInt()
	{
		boost::gregorian::date d(1970,Jan,1);
		boost::posix_time::ptime myTime = microsec_clock::local_time();
		boost::posix_time::ptime myEpoch(d); 
		boost::posix_time::time_duration myTimeFromEpoch = myTime - myEpoch;
		boost::int64_t myTimeAsInt = myTimeFromEpoch.ticks();
	return (myTimeAsInt%10000000000) ;
	}



	void cutDeprecatedUserHistory(const std::string & ip)
    	{
		std::string ip_ = ip;
		ip_.append("_");
		//LOG(INFO) << "cutDeprecatedUserHistory start\n";

		redis::client & db_views = *views;
		int k=0;
		try{
			
			redis::client::string_vector history;
			if (db_views.exists(ip)&&db_views.exists(ip_))
			{
				if ((k=(db_views.zcount(ip_, 0,INFINITY) - VIEWS_LIMIT))<0) return;
				//LOG(INFO)<<"views history more than"<<k<<endl;
				db_views.zrange(ip_, 0, k, history);

				for (unsigned int i=0; i<history.size();i++)
				{
					//LOG(INFO)<<"deleted element "<<history[i];

					try{
						db_views.zrem(ip,history[i]);
					}catch (redis::redis_error & e) 
					{
						//LOG(INFO) << " not found in ip";
					}
					try{

						db_views.zrem(ip_,history[i]);
					}catch (redis::redis_error & e) 
					{
						//LOG(INFO) << " not found in ip_";
					}

									
				}
			}else 	{/*LOG(INFO) << "keys doesn't exists!\n";*/}


		}catch (redis::redis_error & e) 
		{
			LOG(ERROR) << "Redis cutDeprecatedUserHistory failed!";
		}

		//LOG(INFO) << "cutDeprecatedUserHistory end\n";

    }

string CutLocation (const string& str)
{
  size_t found;
  //LOG(INFO)<< "Splitting: " << str << endl;

	size_t  tes = str.find("/" , str.find("http://")+7);

	string str1 = str.substr(0, str.size()-1);

  found=str1.find_last_of("/\\");
//LOG(INFO)<< "tes = " << tes << "  found = "<<found << endl;

if (found < tes) return "";
  return str1.substr(0,found+1);
}


};
#endif // DBWrapper_H

}  // end namespace mongo
