#include "DB.h"
#include "Core.h"
#include "Offer.h"
#include <boost/crc.hpp>
#include <boost/foreach.hpp>
#include <boost/date_time/posix_time/ptime.hpp>
#include <boost/date_time/posix_time/posix_time_io.hpp>
#include <boost/format.hpp>
#include <boost/algorithm/string.hpp>
#include <boost/regex.hpp>
#include <boost/regex/icu.hpp>
#include <glog/logging.h>
#include <string>
#include <iostream>
#include <stdio.h>
#include <ctime>
#include <cstdlib>
#include <sstream>
#include <time.h>
#include <fstream>
#include <mongo/util/version.h>
#define _UNICODE

using std::list;
using std::vector;
using std::map;
using std::unique_ptr;
using std::string;
using namespace boost::posix_time;
#define foreach	BOOST_FOREACH
using namespace std;

int Core::request_processed_ = 0;
    
Core::Core(const std::string &index_folder_offer, const std::string &index_folder_informer)
    : amqp_initialized_(false), amqp_down_(true), amqp_(0),
    index_folder_offer_(index_folder_offer), index_folder_informer_(index_folder_informer)
{   
    InitMessageQueue();

}

Core::~Core()
{

	LOG(INFO)<<"Object AMQP was deleted";
	exchange_->Delete("indexator");
    delete amqp_;
}

/** \brief Метод в бесконечном цикле вызывает ProcessMQ() каждые 300 мсек*/
int Core::Process()
{
    try
    {
        CreateIndexForOffers(true);
    }
    catch(const std::exception& ex)
    {
        LOG(ERROR) << "Ошибка при запросе к lucene: " << ex.what();
    }
    try
    {
	    CreateIndexForInformers(true);
    }
    catch(const std::exception& ex)
    {
        LOG(ERROR) << "Ошибка при запросе к lucene: " << ex.what();
    }
    try
    {
        LOG(INFO) << "Запускаем indexer";
	    string r;
        r = exec();
        LOG(INFO) << r;
    }
    catch(const std::exception& ex)
    {
        LOG(ERROR) << "Ошибка при запросе к Sphinx Indexer: " << ex.what();
    }
	while(1)
	{       
        try
        {
            ProcessMQ();
        }
        catch(const std::exception& ex)
        {
            LOG(ERROR) << "Ошибка при запросе к lucene: " << ex.what();
        }
		sleep (60);
	}
	return 0;
}

/** Проверка и обработка сообщений MQ.

    Проверяются сообщения со следующими routing key:

    <table>
    <tr>
        <td> \c advertise.update </td>
        <td> уведомление об изменении в рекламном предложении; </td>
    </tr>
     <tr>
        <td> \c advertise.delete </td>
        <td> уведомление об удалении рекламного предложения; </td>
    </tr>   
    </table>
	
	Обрабатываемое сообщение должно иметь вид:
	Offer:2d6a3523-4bb5-44d9-9a92-44140a89578c;Campaign:31a1534a-cced-4587-ad30-7c1bd805db6a, где 
	Offer - это идентификатор рекламного предложения,
	Campaign - это идентификатор рекламной кампании
	
    На данный момент при получении сообщений \c advertise.delete происходит удаление
    из индекса документа соответствующего заданному рекламному предложению.

    При получении сообщений \c advertise.update происходит обновление соответствующего документа
	в индексе.
    
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
	 
   string logline = boost::str(
	    boost::format("%1% \t %2% ")
	    % second_clock::local_time()
	    % "review messages in AMQP"
	);
	LOG(INFO)<< logline.c_str()<<endl;
	printf ("%s\n", logline.c_str());

    time_last_mq_check_ = second_clock::local_time();


    if (amqp_down_)
        InitMessageQueue();

    try {
	int kk=0;
		//Обработка всех сообщений, находящихся в очереди mq_advertise_
        do{ 
			// Проверка сообщений advertise.#
            mq_advertise_->Get(AMQP_NOACK);
            AMQPMessage *m = mq_advertise_->getMessage();
			kk = m->getMessageCount();
			LOG(INFO) << "ADVERTISE queue: message count =" << m->getMessageCount();

            if (m->getMessageCount() > -1) {
                LOG(INFO) << "Message retrieved:";
                LOG(INFO) << "  body:        " << m->getMessage();
                LOG(INFO) << "  routing key: " <<  m->getRoutingKey();
                LOG(INFO) << "  exchange:    " <<  m->getExchange();
                
				// Обновление индекса по сообщению advertise.#
				ModifyOfferIndex(m->getMessage(), m->getRoutingKey());
                time_last_mq_check_ = second_clock::local_time();
                check_interval = 2;
                try
                {
                    LOG(INFO) << "Запускаем indexer";
                    string r;
                    r = exec();
                    LOG(INFO) << r;
                }
                catch(const std::exception& ex)
                {
                    LOG(ERROR) << "Ошибка при запросе к Sphinx Indexer: " << ex.what();
                }
                //return true;
            }
			
			if (kk==0 || kk==-1) break; 
        }while (kk>0);

		//Обработка всех сообщений, находящихся в очереди mq_campaign_
         do{ 
			// Проверка сообщений campaign.#
            mq_campaign_->Get(AMQP_NOACK);
            AMQPMessage *m = mq_campaign_->getMessage();
			kk = m->getMessageCount();
			LOG(INFO) << "CAMPAIGN queue: message count =" << m->getMessageCount();

            if (m->getMessageCount() > -1) {
                LOG(INFO) << "Message retrieved:";
                LOG(INFO) << "  body:        " << m->getMessage();
                LOG(INFO) << "  routing key: " <<  m->getRoutingKey();
                LOG(INFO) << "  exchange:    " <<  m->getExchange();
                
				// Обновление индекса по сообщению campaign.#
				ModifyOfferIndex(m->getMessage(), m->getRoutingKey());
                time_last_mq_check_ = second_clock::local_time();
                check_interval = 2;
                try
                {
                    LOG(INFO) << "Запускаем indexer";
                    string r;
                    r = exec();
                    LOG(INFO) << r;
                }
                catch(const std::exception& ex)
                {
                    LOG(ERROR) << "Ошибка при запросе к Sphinx Indexer: " << ex.what();
                }
            }
			
			if (kk==0 || kk==-1) break;
			
		}while (kk>0);   
  
		//Обработка всех сообщений, находящихся в очереди mq_informer_
         do{ 
			// Проверка сообщений informer_rating.#
            mq_informer_->Get(AMQP_NOACK);
            AMQPMessage *m = mq_informer_->getMessage();
			kk = m->getMessageCount();
			LOG(INFO) << "INFORMER queue: message count =" << m->getMessageCount();

            if (m->getMessageCount() > -1) {
                LOG(INFO) << "Message retrieved:";
                LOG(INFO) << "  body:        " << m->getMessage();
                LOG(INFO) << "  routing key: " <<  m->getRoutingKey();
                LOG(INFO) << "  exchange:    " <<  m->getExchange();
                
				// Обновление индекса по сообщению campaign.#
				ModifyInformerIndex(m->getMessage(), m->getRoutingKey());
                time_last_mq_check_ = second_clock::local_time();
                check_interval = 2;
                
            }
			
			if (kk==0 || kk==-1) return true;
		}while (kk>0);  
 
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


/**  Построение индекса по всем рекламным предложениям, находящимся в базе.
	Индекс имеет следующие поля:
	<table>
    <tr>
        <td> \c guid </td>
        <td> идентификатор рекламного предложения </td>
    </tr>
     <tr>
        <td> \c broadMatch </td>
        <td> ключевые слова и фразы рекламного предложения </td>
    </tr>   
	<tr>
        <td> \c phraseMatch </td>
        <td> "фразовые соответствия" рекламного предложения </td>
    </tr> 
	<tr>
        <td> \c exactMatch </td>
        <td> "точные фразы" рекламного предложения </td>
    </tr> 
	<tr>
        <td> \c minusMatch </td>
        <td> минус-слова рекламного предложения </td>
    </tr> 
	<tr>
        <td> \c informer_ids </td>
        <td> информеры, за которыми закреплено данное рекламное предложение </td>
    </tr> 	
	<tr>
        <td> \c campaign_id </td>
        <td> идентификатор рекламной кампании </td>
    </tr> 
    </table>
	

    Для полей titleMatch, descriptionMatch, broadMatch, phraseMatch, minusMatch используется SnowballAnalyzer, который позволяет индексировать
    с отсечением окончаний и удалением стоп-слов.
*/
void Core::CreateIndexForOffers(const bool clearIndex)
{   
	IndexWriter* writer = NULL;
    const char* target = index_folder_offer_.c_str();
	PerFieldAnalyzerWrapper * an = new PerFieldAnalyzerWrapper(new WhitespaceAnalyzer());
    if ( !clearIndex && IndexReader::indexExists(target) )
    {
            if ( IndexReader::isLocked(target) )
            {
                //printf("Index was locked... unlocking it.\n");
                IndexReader::unlock(target);
            }	
            writer = _CLNEW IndexWriter( target, an, false);
    }
    else
    {
            writer = _CLNEW IndexWriter( target ,an, true);
	}	

    //Максимальное число индексируемых термов (слов)
	writer->setMaxFieldLength(0x7FFFFFFFL); // LUCENE_INT32_MAX_SHOULDBE
    //Обьеденение сигментов в один файл
    writer->setUseCompoundFile(false);
	
	mongo::DB db;
	int count = 0, skipped = 0;
	
	// Инициализация курсора по всем рекламным предложениям базы Mongo
	auto cursor = db.query("offer", mongo::Query());
    
	// Структура для хранения ключевых слов, точных фраз и минус-слов рекламного предложения
	OfferKeywordsData data;
	
	
    //Цикл по рекламным предложениям
	while (cursor->more())
    {

		//рекламные предложения с пустым полем guid отбрасываются
		mongo::BSONObj x = cursor->next();
		string id = x.getStringField("guid");
		if (id.empty())
        {
			skipped++;
			continue;
		}
		
		
		//рекламные предложения с пустым полем image отбрасываются
		string image = x.getStringField("image");
        string swf = x.getStringField("swf");
		if (image.empty())
        {
            if (swf.empty()){
                skipped++;
                continue;
            }
		}
    
        data.guid.clear();
        data.guid = x.getStringField("guid");                                   //Заполнение идентификатора рекламного предложения
        data.campaign_id.clear();
        data.campaign_id = x.getStringField("campaignId");                      //Заполнение идентификатора рекламной кампании
        data.type.clear();
        data.type = x.getStringField("type");                                   //Заполнение типа рекламного предложения
        data.rating.clear();
        data.rating = to_string(mongo::DB::toFloat(x.getField("rating")));      //Заполнение рейтинга РП по ПС
        data.isOnClick.clear();
        data.isOnClick = to_string(mongo::DB::toBool(x.getField("isOnClick"))); //Заполнение поля реклама по кликам или по показам
        data.contextOnly.clear();
        data.contextOnly = to_string(mongo::DB::toBool(x.getField("contextOnly"))); //Заполнение поля только контекстная реклама
        data.retargeting.clear();
        data.retargeting = to_string(mongo::DB::toBool(x.getField("retargeting"))); //Заполнение поля только контекстная реклама
        data.category_ids.clear();
        data.category_ids = x.getStringField("category"); 
        //-----------------------------------------------------------------------------------------------------------------------------
        //Заполнение списка информеров, закоторыми закреплено рекламное предложение
        //----------------------------------------------------------------------------------------------------------------------------	
        mongo::BSONObjIterator iterA = x.getObjectField("listAds");
        data.informer_ids.clear();
        while (iterA.more())
        {
            (data.informer_ids).insert(iterA.next().str());
        }
        //Создание документа для индекса
        createOfferDocument(doc, data);
        //Добавление документа в индекс
        try
        {
            writer->addDocument( &doc );
        }
        catch(CLuceneError &err)
            {
                LOG(INFO) << "Lucene adding document to index error:  " << err.what() << "\n";
            }
        catch (...) {
                LOG(INFO)<<"adding offer failed"<<"   ="<<data.guid.c_str()<<"=";
        }
        count++;
    } // Конец цикла по рекламным предложениям
	LOG(INFO) << "Loaded " << count << " offers";
    //Оптимизируем индекс
	try
    {
		delete an;
		writer->setUseCompoundFile(true);
		writer->optimize();
    		writer->close();
		_CLLDELETE(writer);
	}
    catch(...)
	{
		
		LOG(WARNING)<<"CLucene closing error"<<endl;
	}
    if (skipped)
        LOG(WARNING) << skipped << " offers with empty id or image skipped";
}

void Core::CreateIndexForInformers(const bool clearIndex)
{
	IndexWriter* writer = NULL;
	const char* target = index_folder_informer_.c_str();
	PerFieldAnalyzerWrapper * an = new PerFieldAnalyzerWrapper(new WhitespaceAnalyzer());
	if ( !clearIndex && IndexReader::indexExists(target) )
    {
		if ( IndexReader::isLocked(target) ){
			//printf("Index was locked... unlocking it.\n");
			IndexReader::unlock(target);
		}
		writer = _CLNEW IndexWriter( target, an, false);
	}
    else
    {
		writer = _CLNEW IndexWriter( target ,an, true);
	}	

	writer->setMaxFieldLength(0x7FFFFFFFL); // LUCENE_INT32_MAX_SHOULDBE
    writer->setUseCompoundFile(false);
	
	mongo::DB db;
	int count = 0;
 	//Mongo
	auto cursor = db.query("informer.rating", mongo::Query());

	OfferInformerRating data;

	while (cursor->more())
    {
		mongo::BSONObj x = cursor->next();
		data.informer = x.getStringField("guid");
		mongo::BSONObj offer_set = x.getObjectField("rating");
		set<string> offer_ids;
		offer_set.getFieldNames(offer_ids);
		set<string>::iterator it;
  		for ( it=offer_ids.begin() ; it != offer_ids.end(); it++ )
		{
    		//LOG(INFO) <<*it <<"  -> "<< mongo::DB::toFloat(offer_set.getField(*it));
			data.offer = *it;
			data.rating = to_string(mongo::DB::toFloat(offer_set.getField(*it)));
			//LOG(INFO) <<"to index (offer, informer, rating) -> " << data.offer <<"  " <<data.informer <<"  " <<data.rating;
			LOG(INFO) << data.offer <<"  " <<data.informer <<"  " <<data.rating;
            //Создаём документ для индекса
            createRatingDocument(doc, data);
            //Добавляем документ в индекс
            try
            {
                writer->addDocument( &doc );
            }
            catch(CLuceneError &err)
                {
                    LOG(INFO) << "Lucene adding document to index error:  " << err.what() << "\n";
                }
            catch (...) {
                    LOG(INFO)<<"       adding offer failed"<<"   ="<<data.offer.c_str()<<"=";
            }
        }
  		count++;
	} // while

	LOG(INFO) << "Loaded " << count << " accordings";

	try
    {
		delete an;
		writer->setUseCompoundFile(true);
		writer->optimize();
    	writer->close();
		_CLLDELETE(writer);
	}
    catch(...)
	{
		
		LOG(WARNING)<<"CLucene closing error"<<endl;
	}
}


/**
	\brief Создаёт документ для индекса
*/
void Core::createOfferDocument(Document &doc, OfferKeywordsData &offer)
{
	doc.clear();

	char f[100];
	TCHAR tf[CL_MAX_DIR];

	strcpy(f, offer.guid.c_str());
	lucene_utf8towcs(tf,f,CL_MAX_DIR);
	doc.add( *_CLNEW Field(_T("guid"), tf, Field::STORE_YES | Field::INDEX_UNTOKENIZED ) );
	//LOG(INFO)<<"guid: "<<"="<<f<<"=";

	strcpy(f, offer.campaign_id.c_str());
	lucene_utf8towcs(tf,f,CL_MAX_DIR);
	doc.add( *_CLNEW Field(_T("campaign_id"), tf, Field::STORE_YES | Field::INDEX_UNTOKENIZED ) );
	//LOG(INFO)<<"campaign: "<<"="<<f<<"=";

	strcpy(f, offer.type.c_str());
	lucene_utf8towcs(tf,f,CL_MAX_DIR);
	doc.add( *_CLNEW Field(_T("type"), tf, Field::STORE_YES | Field::INDEX_UNTOKENIZED ) );
	//LOG(INFO)<<"type: "<<"="<<f<<"=";
    
    TCHAR * temp;
	temp = stringUnion(offer.informer_ids);
	doc.add( *_CLNEW Field(_T("informer_ids"), temp , Field::STORE_YES | Field::INDEX_TOKENIZED) );
	//LOG(INFO)<<"informer_ids: "<<"   ="<<temp<<"=";
	delete [] temp;

	strcpy(f, offer.category_ids.c_str());
	lucene_utf8towcs(tf,f,CL_MAX_DIR);
	doc.add( *_CLNEW Field(_T("category_ids"), tf , Field::STORE_YES | Field::INDEX_TOKENIZED) );
	//LOG(INFO)<<"informer_ids: "<<"   ="<<temp<<"=";
	
	strcpy(f, offer.rating.c_str());
	lucene_utf8towcs(tf,f,CL_MAX_DIR);
	doc.add( *_CLNEW Field(_T("rating"), tf , Field::STORE_YES | Field::INDEX_UNTOKENIZED) );
	//LOG(INFO)<<"rating: "<<"   ="<<h<<"=";
    strcpy(f, offer.isOnClick.c_str());
	lucene_utf8towcs(tf,f,CL_MAX_DIR);
	doc.add( *_CLNEW Field(_T("isonclick"), tf, Field::STORE_YES | Field::INDEX_UNTOKENIZED) );

    strcpy(f, offer.contextOnly.c_str());
	lucene_utf8towcs(tf,f,CL_MAX_DIR);
	doc.add( *_CLNEW Field(_T("contextonly"), tf, Field::STORE_YES | Field::INDEX_UNTOKENIZED) );

    strcpy(f, offer.retargeting.c_str());
	lucene_utf8towcs(tf,f,CL_MAX_DIR);
	doc.add( *_CLNEW Field(_T("retargeting"), tf, Field::STORE_YES | Field::INDEX_UNTOKENIZED) );
}

void Core::createRatingDocument( Document &doc, OfferInformerRating &data)
{
	doc.clear();

	char f[50];
	TCHAR tf[CL_MAX_DIR];

	strcpy(f, data.offer.c_str());
	lucene_utf8towcs(tf,f,CL_MAX_DIR);
	doc.add( *_CLNEW Field(_T("offer"), tf, Field::STORE_YES | Field::INDEX_TOKENIZED ) );

	strcpy(f, data.informer.c_str());
	lucene_utf8towcs(tf,f,CL_MAX_DIR);
	doc.add( *_CLNEW Field(_T("informer"), tf, Field::STORE_YES | Field::INDEX_TOKENIZED ) );

	strcpy(f, data.rating.c_str());
	lucene_utf8towcs(tf,f,CL_MAX_DIR);
	doc.add( *_CLNEW Field(_T("rating"), tf, Field::STORE_YES | Field::INDEX_UNTOKENIZED ) );
}

/**
	\brief Обновление индекса. 

	Метод вызывается автоматически при наличии сообщения в очереди AMQP.
*/
void Core::ModifyOfferIndex(std::string message, std::string command)
{

	const char* target = index_folder_offer_.c_str();

	LOG(INFO)<<"Обновление индекса по сообщению: "<<message;
	string::size_type pos;
	std::string offer_guid;
	std::string campaign_guid;
	std::string queue;

	const string      sDelim1( "." );
	const string      sDelim2( ";" );
	const string      sDelim3( ":" );


	//Определение типа очереди и типа сообщения 
	pos = command.find_first_of( sDelim1 );
	queue = command.substr( 0, pos); //advertise or campaign
	command  = command.substr( pos+1, command.size() ); //update or delete

	//LOG(INFO)<<"queue = "<<queue<<"   command="<<command<<endl;
	//printf("%s %s\n",queue.c_str(), command.c_str());

	if (strcmp(queue.c_str(),"advertise")==0)
	{
		//Сообщение имеет формат --> Offer:2d6a3523-4bb5-44d9-9a92-44140a89578c;Campaign:31a1534a-cced-4587-ad30-7c1bd805db6a
		pos = message.find_first_of( sDelim2 );
		//LOG(INFO)<<"pos = "<<pos;
		offer_guid  = message.substr( message.find_first_of( sDelim3 )+1, pos-6); 
		//message = message.substr( message.find_first_of( sDelim2 )+1, message.size());
		pos = message.find_last_of( sDelim3 );
		campaign_guid  = message.substr( pos+1, message.size()-pos);
		LOG(INFO)<<"offer_guid=("<<offer_guid<<")  campaign_guid="<<campaign_guid<<endl;
	}
	
	
	PerFieldAnalyzerWrapper * an = new PerFieldAnalyzerWrapper(new WhitespaceAnalyzer());

	IndexModifier* indexModifier = new IndexModifier(target, an, false);
	char f[50];
	TCHAR tf[CL_MAX_DIR];

	
	int32_t deleted = 0;
	if (strcmp(queue.c_str(),"advertise")==0) 
	{
		strcpy(f, offer_guid.c_str());
		lucene_utf8towcs(tf,f,CL_MAX_DIR);
		deleted = indexModifier->deleteDocuments(new Term(_T("guid"),tf));
	}
	else if (strcmp(queue.c_str(),"campaign")==0) 
	{
		strcpy(f, message.c_str());
		lucene_utf8towcs(tf,f,CL_MAX_DIR);
		deleted = indexModifier->deleteDocuments(new Term(_T("campaign_id"),tf));
	}
	LOG(INFO)<<"from indef was deleted docs - "<<deleted;

	if (command.compare("delete")==0) 
	{
			indexModifier->flush();
			indexModifier->close();
			return;
	}

	
	mongo::DB db;
	auto cursor = db.query("offer",QUERY("guid" << offer_guid));
	if (strcmp(queue.c_str(),"campaign")==0) cursor = db.query("offer", QUERY("campaignId" << message));

   	int  skipped = 0;

	OfferKeywordsData data;

 	//Цикл по рекламным предложениям
	while (cursor->more()) {

		//рекламные предложения с пустым полем guid отбрасываются
		mongo::BSONObj x = cursor->next();
		string id = x.getStringField("guid");
		if (id.empty()) {
			skipped++;
			continue;
		}

		//рекламные предложения с пустым полем image отбрасываются
		string image = x.getStringField("image");
        string swf = x.getStringField("swf");
		if (image.empty())
        {
            if (swf.empty()){
                skipped++;
                continue;
            }
		}

	data.guid.clear();
	data.guid = x.getStringField("guid");                                   //Заполнение идентификатора рекламного предложения
    data.campaign_id.clear();
	data.campaign_id = x.getStringField("campaignId");                      //Заполнение идентификатора рекламной кампании
    data.type.clear();
	data.type = x.getStringField("type");                                   //Заполнение типа рекламного предложения
    data.rating.clear();
	data.rating = to_string(mongo::DB::toFloat(x.getField("rating")));      //Заполнение рейтинга РП по ПС
    data.isOnClick.clear();
    data.isOnClick = to_string(mongo::DB::toBool(x.getField("isOnClick"))); //Заполнение поля реклама по кликам или по показам
    data.contextOnly.clear();
    data.contextOnly = to_string(mongo::DB::toBool(x.getField("contextOnly"))); //Заполнение поля только контекстная реклама
    data.retargeting.clear();
    data.retargeting = to_string(mongo::DB::toBool(x.getField("retargeting"))); //Заполнение поля только контекстная реклама
    data.category_ids.clear();
    data.category_ids = x.getStringField("category"); 

	//-----------------------------------------------------------------------------------------------------------------------------
    //Заполнение списка информеров, закоторыми закреплено рекламное предложение
	//----------------------------------------------------------------------------------------------------------------------------	
    mongo::BSONObjIterator iterA = x.getObjectField("listAds");
	data.informer_ids.clear();
	while (iterA.more()) {
		(data.informer_ids).insert(iterA.next().str());
    	}
    //Создание документа для индекса
    createOfferDocument(doc, data);
    //Добавление документа в индекс
    try
    {
        indexModifier->addDocument( &doc );
    }
    catch(CLuceneError &err)
        {
            LOG(INFO) <<"Lucene adding document to index error:  " << err.what();
        }
    catch (...) {
            LOG(INFO)<<"adding offer failed"<<"   ="<<data.guid.c_str()<<"=";
    }
    
	
	} // Конец цикла по рекламным предложениям 
	
	indexModifier->flush();
	indexModifier->optimize();
	indexModifier->close();
	_CLLDELETE(indexModifier);
	LOG(INFO)<<"Модификация индекса завершена";
	delete an;
}

void Core::ModifyInformerIndex(std::string message, std::string command)
{
	const char* target = index_folder_informer_.c_str();

	LOG(INFO)<<"Обновление индекса по сообщению: "<<message;
	string::size_type pos;
	std::string offer_guid;
	std::string informer_guid;
	std::string queue;

	const string      sDelim1( "." );
	const string      sDelim2( ";" );
	const string      sDelim3( ":" );


	//Определение типа очереди и типа сообщения 
	pos = command.find_first_of( sDelim1 );
	queue = command.substr( 0, pos); //  informer_rating
	command  = command.substr( pos+1, command.size() ); //update or delete

	PerFieldAnalyzerWrapper * analyzer= new PerFieldAnalyzerWrapper(new WhitespaceAnalyzer());
	IndexModifier* indexModifier = new IndexModifier(target, analyzer, false);
	char f[50];
	TCHAR tf[CL_MAX_DIR];
	int32_t deleted = 0;
	strcpy(f, message.c_str());
	lucene_utf8towcs(tf,f,CL_MAX_DIR);
	deleted = indexModifier->deleteDocuments(new Term(_T("informer"),tf));
	LOG(INFO)<<"from indef was deleted docs - "<<deleted;

	if (command.compare("delete")==0) 
	{
			indexModifier->flush();
			indexModifier->close();
			return;
	}
	
	mongo::DB db;
	auto cursor = db.query("informer.rating",QUERY("guid" << message));
 	
	OfferInformerRating data;
    
	while (cursor->more())
    {
		mongo::BSONObj x = cursor->next();
		data.informer = x.getStringField("guid");
		mongo::BSONObj offer_set = x.getObjectField("rating");
		set<string> offer_ids;
		offer_set.getFieldNames(offer_ids);
		set<string>::iterator it;
  		LOG(INFO) << "myset contains:";
  		for ( it=offer_ids.begin() ; it != offer_ids.end(); it++ )
		{
    		//LOG(INFO) <<*it <<"  -> "<< mongo::DB::toFloat(offer_set.getField(*it));
			data.offer = *it;
			data.rating = to_string(mongo::DB::toFloat(offer_set.getField(*it)));
			LOG(INFO) <<"to index (offer, informer, rating) -> " << data.offer <<"  " <<data.informer <<"  " <<data.rating;
            //Создаём документ для индекса
            createRatingDocument(doc, data);
            //Добавляем документ в индекс
            try
            {
                indexModifier->addDocument( &doc );
            }
            catch(CLuceneError &err)
                {
                    LOG(INFO) << "Lucene adding document to index error:  " << err.what() << "\n";
                }
            catch (...) {
                    LOG(INFO)<<"       adding offer failed"<<"   ="<<data.offer.c_str()<<"=";
            }
		}
	} // while
	indexModifier->flush();
	indexModifier->optimize();
	indexModifier->close();
	_CLLDELETE(indexModifier);
	LOG(INFO)<<"Модификация индекса завершена";
	delete analyzer;
}


/** \brief  Инициализация очереди сообщений (AMQP).

    Если во время инициализации произошла какая-либо ошибка, то сервис
    продолжит работу, но возможность оповещения об изменениях и горячего
    обновления будет отключена.
*/

void Core::InitMessageQueue()
{
	int not_init = 0;
	// Объявляем точку обмена
	LOG(INFO)<<"=== InitMessageQueue ===== ";
	while(not_init < 100)
	{
    	try
        {
            LOG(INFO)<<"Creating object AMQP...  ";
            amqp_ = new AMQP("guest:guest@localhost//");
            LOG(INFO)<<"Creating exchange... ";
            exchange_ = amqp_->createExchange();
            LOG(INFO)<<"Declaring exchange... ";
            exchange_->Declare("indexator", "topic", AMQP_AUTODELETE);
            break;
 	    }
        catch (AMQPException &ex)
        {
            LOG(INFO) << "Error in exchange init: " + ex.getMessage();
            delete amqp_;
            not_init++;
            sleep(30);
    	}
	}

	if (not_init==100) return;
	else LOG(INFO) << "Exchange was declared succesfully!!! ";
	try
    {
        // Составляем уникальные имена для очередей
        ptime now = microsec_clock::local_time();
        std::string postfix = to_iso_string(now);
        boost::replace_first(postfix, ".", ",");
        std::string mq_advertise_name( "getmyad.advertise." + postfix );
        std::string mq_campaign_name( "getmyad.campaign." + postfix );
        std::string mq_informer_name( "getmyad.informer_rating." + postfix );


        // Объявляем очереди
        mq_advertise_ = amqp_->createQueue();
        mq_advertise_->Declare(mq_advertise_name, AMQP_AUTODELETE | AMQP_EXCLUSIVE);
        mq_campaign_ = amqp_->createQueue();
        mq_campaign_->Declare(mq_campaign_name, AMQP_AUTODELETE | AMQP_EXCLUSIVE);
        mq_informer_ = amqp_->createQueue();
        mq_informer_->Declare(mq_informer_name, AMQP_AUTODELETE | AMQP_EXCLUSIVE);

        // Привязываем очереди
        exchange_->Bind(mq_advertise_name, "advertise.#");
        exchange_->Bind(mq_campaign_name, "campaign.#");
        mq_informer_->Declare(mq_informer_name, AMQP_AUTODELETE | AMQP_EXCLUSIVE);

        // Привязываем очереди
        exchange_->Bind(mq_advertise_name, "advertise.#");
        exchange_->Bind(mq_campaign_name, "campaign.#");
        exchange_->Bind(mq_informer_name, "informer_rating.#");
        
        if (mq_campaign_==NULL) printf("Campaign queue is null!\n");
        else printf("Campaign queue not null!\n");
        if (mq_advertise_==NULL) printf("advertise queue is null!\n");
        else printf("advertise queue not null!\n");
        if (mq_informer_==NULL) printf("informer_rating queue is null!\n");
        else printf("informer_rating queue not null!\n");

        amqp_initialized_ = true;
        amqp_down_ = false;

        LOG(INFO) << "Created ampq queues: " <<
            mq_advertise_name << ", ";
        LogToAmqp("Created amqp queue " + mq_advertise_name);
    }
    catch (AMQPException &ex)
    {
        LOG(ERROR) << ex.getMessage();
        LOG(ERROR) << "Error in AMPQ init. Feature will be disabled.";
        LOG(INFO) << "Error in AMQP init: " + ex.getMessage();
        LogToAmqp("Error in AMQP init: " + ex.getMessage());
        amqp_initialized_ = false;
        amqp_down_ = true;
    }
	LOG(INFO)<<"=== InitMessageQueue finished ===== ";

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

/**
	\brief Метод объединения строк. 
	
	Используется при добавлении списка в поле индекса.
*/

TCHAR* Core::stringUnion (const std::set<std::string> &myset)
{
	std::string temp;
	StringBuffer str;
	TCHAR * tf = new TCHAR[CL_MAX_DIR];
    	char * f = new char [CL_MAX_DIR];

	strcpy(f,"");

	set<string>::iterator it;

for ( it=myset.begin() ; it != myset.end(); it++ )
	{
		string t = *it;
		boost::trim(t);
		if ((strlen(f) + strlen(t.c_str())) >CL_MAX_DIR-1) {/*LOG(ERROR)<<"Too big";*/ break;}
		strcat(f,t.c_str());
		strcat(f," ");
	}

	
	lucene_utf8towcs(tf,f,CL_MAX_DIR);
	_tCharToLow(tf);

	delete(f);

	return tf;
 }

/**
	\brief Перевод строки в нижний регистр
*/
void Core::_tCharToLow (TCHAR* str)
{
	for (unsigned int i=0 ; i<_tcslen(str); i++ )
	{
		str[i]=cl_tolower(str[i]);
	}
}


/**
	\brief Перевод в строку
*/
string Core::to_string(const float& value)
{
    char buf[18]; // все равно максимальная точность на Intel платформе 17 знаков
    sprintf(buf,"%17.2f",value);
    string t(buf);
    boost::trim(t);
    return t;
}
string Core::to_string(const bool& value)
{   
    string t;
    if (value)
    {
        t = "true";    
    }
    else
    {
        t = "false";
    }
    boost::trim(t);
    return t;
}
string Core::exec() {

    return string();

    FILE* pipe = popen("indexer --all --rotate", "r");
    if (!pipe) return "ERROR";
    char buffer[512];
    string result = "";
    while(!feof(pipe)) {
        if(fgets(buffer, 512, pipe) != NULL)
            result += buffer;
    }
    pclose(pipe);
    return result;
}
