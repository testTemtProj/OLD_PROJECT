#include "DB.h"
#include <glog/logging.h>
#include <boost/algorithm/string.hpp>

#include "IndexCreatorService.h"
#include "Core.h"
//#include <fcgi_stdio.h>

using namespace std;
/**
Инициализация базы данных рекламных предложений. Параметры подключения берутся из файла конфигурации, который задается при старте приложения.
*/
IndexCreatorService::IndexCreatorService(std::string fileName)
  {
	InitDefault();
	InitDBs(fileName);
}

/**
Инициализация базы данных рекламных предложений значениями по умолчанию.
*/ 
void IndexCreatorService::InitDefault()
  {
      mongo_main_host_="localhost";
      mongo_main_set_="vsrv";
      mongo_main_db_="getmyad_db";
      mongo_main_slave_ok_=true;
      index_folder_offer_="/var/www/index1";
      index_folder_informer_="/var/www/index2";

    }


/**
Инициализация базы данных рекламных предложений значениями из файла.
*/ 
void IndexCreatorService::InitDBs(std::string fileName)
{
	string::size_type posEndIdx;
	string::size_type ipos=0;
	string            dbType, temp, str, sValue, paramName, paramValue;
	string            sKeyWord;
	const string      sDelim( "=" );

	
	std::ifstream input (fileName);
	LOG(INFO)<<"Connection params:"<<endl;
	while(std::getline(input,str)){
	if( str.empty() );                     // Ignore empty lines
	else
	   {
	      posEndIdx = str.find_first_of( sDelim );
	      paramName  = str.substr( ipos, posEndIdx ); // Extract paramName
	      paramValue= str.substr(posEndIdx+1, str.size()); //Extract paramValue
	      boost::trim(paramValue);
		  if (paramName.compare("mongo_main_host")==0) mongo_main_host_=paramValue;
		  else if (paramName.compare("mongo_main_set")==0) mongo_main_set_=paramValue;
		  else if (paramName.compare("mongo_main_db")==0) mongo_main_db_=paramValue;
		  else if (paramName.compare("mongo_main_slave_ok")==0) mongo_main_slave_ok_=true;
		  else if (paramName.compare("index_folder_offer")==0) index_folder_offer_=paramValue;
		  else if (paramName.compare("index_folder_informer")==0) index_folder_informer_=paramValue;

   	}
		LOG(INFO)<<paramName<<"  - "<<paramValue<<endl;
		
		
	}


input.close();
}


IndexCreatorService::~IndexCreatorService()
{
	LOG(INFO)<<"CORE DELETED";
    delete core;
}

/**
Подключение к базе данных рекламных предложений.
*/ 
bool IndexCreatorService::ConnectDatabase()
{
    LOG(INFO) << "Connecting to " << mongo_main_host_ << "/" << mongo_main_db_;

    try {
    	if (mongo_main_set_.empty())
    	    mongo::DB::addDatabase(
		    mongo_main_host_,
		    mongo_main_db_,
		    mongo_main_slave_ok_);
    	else
    	    mongo::DB::addDatabase(
		    mongo::DB::ReplicaSetConnection(
			    mongo_main_set_,
			    mongo_main_host_),
		    mongo_main_db_,
		    mongo_main_slave_ok_);


	// Проверяем доступность базы данных
    	mongo::DB db;
    	db.findOne("domain.categories", mongo::Query());

    } catch (mongo::UserException &ex) {
    	LOG(ERROR) << "Error connecting to mongo:";
    	LOG(ERROR) << ex.what();
    	return false;
    }

    return true;
}

/**
Метод запускает ядро на выполнение при условии удачного подключения к базе данных.
*/ 
int IndexCreatorService::Serve()
{
    if (!ConnectDatabase()) {
		LOG(INFO) << "Error connecting to DB";
    }
	

		core = new Core(index_folder_offer_, index_folder_informer_);
    	return core->Process();
    }








