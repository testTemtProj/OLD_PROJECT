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
#include<time.h>
#include <mongo/util/version.h>
#include "Core.h"
#include "OfferKeywords.h"


using std::list;
using std::vector;
using std::map;
using std::unique_ptr;
using std::string;//добавлено realinvestsoft
using namespace boost::posix_time;

#define foreach	BOOST_FOREACH

using namespace std;

int Core::request_processed_ = 0;

Core::Core(const std::string &index_folder_offer, const std::string &index_folder_informer)
    : amqp_initialized_(false), amqp_down_(true), amqp_(0),
    index_folder_offer_(index_folder_offer), index_folder_informer_(index_folder_informer)
{
	InitMessageQueue();
    	CreateIndexForOffers(true);
	CreateIndexForInformers(true);

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

	while(1)
	{
    		ProcessMQ();
			sleep (300);
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
        <td> \c keywords </td>
        <td> ключевые слова и фразы рекламного предложения </td>
    </tr>   
	<tr>
        <td> \c exactly_phrases </td>
        <td> "точные фразы" рекламного предложения </td>
    </tr> 
	<tr>
        <td> \c minus_words </td>
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
	

*  Для полей keywords и minus_words используется SnowballAnalyzer, который позволяет индексировать
	с отсечением окончаний и удалением стоп-слов.
*/
void Core::CreateIndexForOffers(const bool clearIndex)
{
	IndexWriter* writer = NULL;
	const char* target = index_folder_offer_.c_str();
	//LOG(INFO)<<"Inside CreateIndexForOffers target = "<<target;

	PerFieldAnalyzerWrapper * an = new PerFieldAnalyzerWrapper(new WhitespaceAnalyzer());
	an->addAnalyzer( _T("keywords"), new lucene::analysis::snowball::SnowballAnalyzer(_T("Russian")) );
	an->addAnalyzer( _T("keywords_eng"), new lucene::analysis::snowball::SnowballAnalyzer() );
	an->addAnalyzer(_T("exactly_phrases"), new WhitespaceAnalyzer());
	an->addAnalyzer(_T("minus_words"), new lucene::analysis::snowball::SnowballAnalyzer(_T("Russian")));
	an->addAnalyzer(_T("informer_ids"), new WhitespaceAnalyzer());
	
	if ( !clearIndex && IndexReader::indexExists(target) ){
		if ( IndexReader::isLocked(target) ){
			//printf("Index was locked... unlocking it.\n");
			IndexReader::unlock(target);
		}

		writer = _CLNEW IndexWriter( target, an, false);
	}else{
		writer = _CLNEW IndexWriter( target ,an, true);
	}	


	writer->setMaxFieldLength(0x7FFFFFFFL); // LUCENE_INT32_MAX_SHOULDBE
    writer->setUseCompoundFile(false);
	
	mongo::DB db;
	int count = 0, skipped = 0;
	
	// Инициализация курсора по всем рекламным предложениям базы Mongo
	auto cursor = db.query("offer", mongo::Query());
    
	// Структура для хранения ключевых слов, точных фраз и минус-слов рекламного предложения
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
		if (image.empty()) {
			skipped++;
			continue;
		}

	data.guid = x.getStringField("guid");				//Заполнение идентификатора рекламного предложения
	data.campaign_id = x.getStringField("campaignId");  //Заполнение идентификатора рекламной кампании
	data.title = x.getStringField("title");             //Заполнение заголовка
	data.type = x.getStringField("type");               //Заполнение типа рекламного предложения
	data.keywords.clear();
	

	//LOG(INFO)<<count<<":  "<<data.guid<<"   "<<data.title;
	
	//Заполнение ключевых слов
	//----------------------------------------------------------------------------------------------------------------------------
	mongo::BSONObjIterator iter = x.getObjectField("keywords");
    while (iter.more()) {
		(data.keywords).insert(iter.next().str());
   	}
	if (data.keywords.empty()) (data.keywords).insert("abcde");  // при отсутствии ключевых слов в индекс заносится фраза =abcde=
	else (data.keywords).insert(data.title);

	//Заполнение точных фраз
	//----------------------------------------------------------------------------------------------------------------------------
	iter = x.getObjectField("exactly_phrases");
	data.exactly_phrases.clear();
	while (iter.more()) {
		(data.exactly_phrases).insert(stringWrapper(iter.next().str()));
    }
	if (data.exactly_phrases.empty()) (data.exactly_phrases).insert("abcde"); // при отсутствии точных фраз в индекс заносится фраза =abcde=

	//Заполнение минус слов
	//----------------------------------------------------------------------------------------------------------------------------
	iter = x.getObjectField("minus_words");
	data.minus_words.clear();
	while (iter.more()) {
		(data.minus_words).insert(iter.next().str());
    	}
	if (data.minus_words.empty()) (data.minus_words).insert("abcde"); // при отсутствии минус слов в индекс заносится фраза =abcde=

	//Заполнение списка информеров, закоторыми закреплено рекламное предложение
	//----------------------------------------------------------------------------------------------------------------------------	
	iter = x.getObjectField("listAds");
	data.informer_ids.clear();
	while (iter.more()) {
		(data.informer_ids).insert(iter.next().str());
    	}

	//Заполнение списка тематик, закоторым удовлетворяет рекламное предложение
	//----------------------------------------------------------------------------------------------------------------------------	
	iter = x.getObjectField("topics");
	data.topic_ids.clear();
	while (iter.more()) {
		(data.topic_ids).insert(iter.next().str());
    	}
	if (data.topic_ids.empty()) (data.topic_ids).insert("common"); // при отсутствии тематик в индекс заносится фраза =common=
	

	//-----------------------------------------------------------------------------------------------------------------------------
	data.rating = mongo::DB::toFloat(x.getField("rating"));


	//Добавление документа в индекс
	addDocumentToWriter(writer, data);
	count++;
} // while
	LOG(INFO) << "Loaded " << count << " offers";

	try{
		delete an;
		writer->setUseCompoundFile(true);
		writer->optimize();
    		writer->close();
		_CLLDELETE(writer);
	}catch(...)
	{
		
		LOG(WARNING)<<"CLucene closing error"<<endl;
	}
    if (skipped)
        LOG(WARNING) << skipped << " offers with empty id or image skipped";


	//SearchFiles(index_folder_.c_str());

}

void Core::CreateIndexForInformers(const bool clearIndex)
{
	IndexWriter* writer = NULL;

	const char* target = index_folder_informer_.c_str();

	
	PerFieldAnalyzerWrapper * an = new PerFieldAnalyzerWrapper(new WhitespaceAnalyzer());
	
	
	
	if ( !clearIndex && IndexReader::indexExists(target) ){
		if ( IndexReader::isLocked(target) ){
			//printf("Index was locked... unlocking it.\n");
			IndexReader::unlock(target);
		}

		writer = _CLNEW IndexWriter( target, an, false);
	}else{
		writer = _CLNEW IndexWriter( target ,an, true);
	}	


	writer->setMaxFieldLength(0x7FFFFFFFL); // LUCENE_INT32_MAX_SHOULDBE
    	writer->setUseCompoundFile(false);
	
	mongo::DB db;
	int count = 0;
	
 	// ????????????? ??????? ?? ???? ????????? ???????????? ???? Mongo
	auto cursor = db.query("informer.rating", mongo::Query());
    


	
	OfferInformerRating data;
	
    
	while (cursor->more()) {

	
		mongo::BSONObj x = cursor->next();
		data.informer = x.getStringField("guid");
				//LOG(INFO) << "informer:"<<data.informer;

		mongo::BSONObj offer_set = x.getObjectField("rating");
		set<string> offer_ids;
		offer_set.getFieldNames(offer_ids);
		set<string>::iterator it;

  		//LOG(INFO) << "myset contains:";
  		for ( it=offer_ids.begin() ; it != offer_ids.end(); it++ )
		{
    			//LOG(INFO) <<*it <<"  -> "<< mongo::DB::toFloat(offer_set.getField(*it));
			data.offer = *it;
			data.rating = to_string(mongo::DB::toFloat(offer_set.getField(*it)));
			//LOG(INFO) <<"to index (offer, informer, rating) -> " << data.offer <<"  " <<data.informer <<"  " <<data.rating;
			LOG(INFO) << data.offer <<"  " <<data.informer <<"  " <<data.rating;

			addDocumentToWriterNew(writer, data);
			
		}
  		count++;

	} // while

	LOG(INFO) << "Loaded " << count << " accordings";

	try{
		delete an;
		writer->setUseCompoundFile(true);
		writer->optimize();
    		writer->close();
		_CLLDELETE(writer);
	}catch(...)
	{
		
		LOG(WARNING)<<"CLucene closing error"<<endl;
	}
    




}


/**
	\brief Добавление документа в индекс
*/
void Core::addDocumentToWriter( IndexWriter* writer, OfferKeywordsData &offer)
{
	doc.clear();

	char f[50];
	TCHAR tf[CL_MAX_DIR];

try{
	strcpy(f, offer.guid.c_str());
	lucene_utf8towcs(tf,f,CL_MAX_DIR);
	doc.add( *_CLNEW Field(_T("guid"), tf, Field::STORE_YES | Field::INDEX_UNTOKENIZED ) );
	LOG(INFO)<<"       guid: "<<"   ="<<f<<"=";


	strcpy(f, offer.campaign_id.c_str());
	lucene_utf8towcs(tf,f,CL_MAX_DIR);
	doc.add( *_CLNEW Field(_T("campaign_id"), tf, Field::STORE_NO | Field::INDEX_TOKENIZED ) );
	//LOG(INFO)<<"       campaign: "<<"   ="<<f<<"=";

	strcpy(f, offer.type.c_str());
	lucene_utf8towcs(tf,f,CL_MAX_DIR);
	doc.add( *_CLNEW Field(_T("type"), tf, Field::STORE_NO | Field::INDEX_TOKENIZED ) );
	//LOG(INFO)<<"       type: "<<"   ="<<f<<"=";

	TCHAR * temp;
	temp = stringUnion(offer.keywords);
	doc.add( *_CLNEW Field(_T("keywords"), temp, Field::STORE_NO | Field::INDEX_TOKENIZED) ); 
	//LOG(INFO)<<"       temp1: "<<"   ="<<temp<<"=";
	delete [] temp;

	temp = stringUnion(offer.keywords);
	doc.add( *_CLNEW Field(_T("keywords_eng"), temp, Field::STORE_NO | Field::INDEX_TOKENIZED) );
	//LOG(INFO)<<"       temp2: "<<"   ="<<temp<<"=";
	delete [] temp;

	temp = stringUnion(offer.exactly_phrases);
	doc.add( *_CLNEW Field(_T("exactly_phrases"), temp, Field::STORE_NO | Field::INDEX_TOKENIZED) );
	//LOG(INFO)<<"       temp3: "<<"   ="<<temp<<"=";
	delete [] temp;

	temp = stringUnion(offer.minus_words);
	doc.add( *_CLNEW Field(_T("minus_words"), temp, Field::STORE_NO | Field::INDEX_TOKENIZED) );
	//LOG(INFO)<<"       temp4: "<<"   ="<<temp<<"=";
	delete [] temp;

	temp = stringUnion(offer.informer_ids);
	doc.add( *_CLNEW Field(_T("informer_ids"), temp , Field::STORE_NO | Field::INDEX_TOKENIZED) );
	//LOG(INFO)<<"       temp5: "<<"   ="<<temp<<"=";
	delete [] temp;

	temp = stringUnion(offer.topic_ids);
	doc.add( *_CLNEW Field(_T("topic_ids"), temp , Field::STORE_NO | Field::INDEX_TOKENIZED) );
	//LOG(INFO)<<"       temp6: "<<"   ="<<temp<<"=";
	delete [] temp;

	
	string h = to_string1((int)(offer.rating*100));
	strcpy(f, h.c_str());
	lucene_utf8towcs(tf,f,CL_MAX_DIR);
	doc.add( *_CLNEW Field(_T("rating"), tf , Field::STORE_YES | Field::INDEX_UNTOKENIZED) );
	LOG(INFO)<<"rating: "<<"   ="<<h<<"=";

	
	writer->addDocument( &doc );
	//LOG(INFO)<<"       adding document..."<<"   ="<<"=";
}
catch(CLuceneError &err)
	{
		LOG(INFO) << "Lucene adding document to index error:  " << err.what() << "\n";
	}
catch (...) {
		LOG(INFO)<<"       adding offer failed"<<"   ="<<offer.guid.c_str()<<"=";

}
}

void Core::addDocumentToWriterNew( IndexWriter* writer, OfferInformerRating &data)
{
	doc.clear();

	char f[50];
	TCHAR tf[CL_MAX_DIR];
try{
	strcpy(f, data.offer.c_str());
	lucene_utf8towcs(tf,f,CL_MAX_DIR);
	doc.add( *_CLNEW Field(_T("offer"), tf, Field::STORE_YES | Field::INDEX_TOKENIZED ) );


	strcpy(f, data.informer.c_str());
	lucene_utf8towcs(tf,f,CL_MAX_DIR);
	doc.add( *_CLNEW Field(_T("informer"), tf, Field::STORE_YES | Field::INDEX_TOKENIZED ) );
	

	strcpy(f, data.rating.c_str());
	lucene_utf8towcs(tf,f,CL_MAX_DIR);
	doc.add( *_CLNEW Field(_T("rating"), tf, Field::STORE_YES | Field::INDEX_UNTOKENIZED ) );
	
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

/**
Добавление документа в индекс при обновлении
*/
void Core::addDocumentToModifierWriter( IndexModifier* writer, OfferKeywordsData &offer)
{

	doc.clear();

	char f[50];
	TCHAR tf[CL_MAX_DIR];
try{
	strcpy(f, offer.guid.c_str());
	lucene_utf8towcs(tf,f,CL_MAX_DIR);
	doc.add( *_CLNEW Field(_T("guid"), tf, Field::STORE_YES | Field::INDEX_UNTOKENIZED ) );


	strcpy(f, offer.campaign_id.c_str());
	lucene_utf8towcs(tf,f,CL_MAX_DIR);
	doc.add( *_CLNEW Field(_T("campaign_id"), tf, Field::STORE_NO | Field::INDEX_TOKENIZED ) );
	LOG(INFO)<<"campaign: "<<"  ="<<f<<"=";

	strcpy(f, offer.type.c_str());
	lucene_utf8towcs(tf,f,CL_MAX_DIR);
	doc.add( *_CLNEW Field(_T("type"), tf, Field::STORE_NO | Field::INDEX_TOKENIZED ) );
	LOG(INFO)<<"type: "<<"  ="<<f<<"=";

	TCHAR * temp;
	temp = stringUnion(offer.keywords);
	doc.add( *_CLNEW Field(_T("keywords"), temp, Field::STORE_NO | Field::INDEX_TOKENIZED) ); 
	delete [] temp;

	temp = stringUnion(offer.keywords);
	doc.add( *_CLNEW Field(_T("keywords_eng"), temp, Field::STORE_NO | Field::INDEX_TOKENIZED) );
	delete [] temp;

	temp = stringUnion(offer.exactly_phrases);
	doc.add( *_CLNEW Field(_T("exactly_phrases"), temp, Field::STORE_NO | Field::INDEX_TOKENIZED) );
	delete [] temp;

	temp = stringUnion(offer.minus_words);
	doc.add( *_CLNEW Field(_T("minus_words"), temp, Field::STORE_NO | Field::INDEX_TOKENIZED) );
	delete [] temp;

	temp = stringUnion(offer.informer_ids);
	doc.add( *_CLNEW Field(_T("informer_ids"), temp , Field::STORE_NO | Field::INDEX_TOKENIZED) );
	delete [] temp;

	temp = stringUnion(offer.topic_ids);
	doc.add( *_CLNEW Field(_T("topic_ids"), temp , Field::STORE_NO | Field::INDEX_TOKENIZED) );
	delete [] temp;
	
	writer->addDocument( &doc );
}
catch(CLuceneError &err)
	{
		LOG(INFO) << "Lucene adding document to index error:  " << err.what() << "\n";
	}
catch (...) {
		LOG(INFO)<<"       adding offer failed"<<"   ="<<offer.guid.c_str()<<"=";

}
}

void Core::addDocumentToModifierWriterNew( IndexModifier* writer, OfferInformerRating &data)
{
	doc.clear();

	char f[50];
	TCHAR tf[CL_MAX_DIR];
try{
	strcpy(f, data.offer.c_str());
	lucene_utf8towcs(tf,f,CL_MAX_DIR);
	doc.add( *_CLNEW Field(_T("offer"), tf, Field::STORE_YES | Field::INDEX_TOKENIZED ) );


	strcpy(f, data.informer.c_str());
	lucene_utf8towcs(tf,f,CL_MAX_DIR);
	doc.add( *_CLNEW Field(_T("informer"), tf, Field::STORE_NO | Field::INDEX_TOKENIZED ) );
	

	strcpy(f, data.rating.c_str());
	lucene_utf8towcs(tf,f,CL_MAX_DIR);
	doc.add( *_CLNEW Field(_T("rating"), tf, Field::STORE_YES | Field::INDEX_UNTOKENIZED ) );
	
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
	


	
	PerFieldAnalyzerWrapper * analyzer= new PerFieldAnalyzerWrapper(new WhitespaceAnalyzer());
	analyzer->addAnalyzer( _T("keywords"), new lucene::analysis::snowball::SnowballAnalyzer(_T("Russian")) );
	analyzer->addAnalyzer( _T("keywords_eng"), new lucene::analysis::snowball::SnowballAnalyzer() );
	analyzer->addAnalyzer(_T("exactly_phrases"), new WhitespaceAnalyzer());
	analyzer->addAnalyzer(_T("minus_words"), new lucene::analysis::snowball::SnowballAnalyzer(_T("Russian")));
	analyzer->addAnalyzer(_T("informer_ids"), new WhitespaceAnalyzer());


	IndexModifier* indexModifier = new IndexModifier(target, analyzer, false);
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
		if (image.empty()) {
			skipped++;
			continue;
		}

	data.guid = x.getStringField("guid");				//Заполнение идентификатора рекламного предложения
	data.campaign_id = x.getStringField("campaignId");  //Заполнение идентификатора рекламной кампании
	data.title = x.getStringField("title");             //Заполнение заголовка
	data.type = x.getStringField("type");               //Заполнение типа рекламного предложения
	data.keywords.clear();
	

	LOG(INFO)<<":  "<<data.guid<<"   "<<data.title;
	
	//Заполнение ключевых слов
	//----------------------------------------------------------------------------------------------------------------------------
	mongo::BSONObjIterator iter = x.getObjectField("keywords");
    while (iter.more()) {
		(data.keywords).insert(iter.next().str());
   	}
	if (data.keywords.empty()) (data.keywords).insert("abcde");  // при отсутствии ключевых слов в индекс заносится фраза =abcde=
	else (data.keywords).insert(data.title);

	//Заполнение точных фраз
	//----------------------------------------------------------------------------------------------------------------------------
	iter = x.getObjectField("exactly_phrases");
	data.exactly_phrases.clear();
	while (iter.more()) {
		(data.exactly_phrases).insert(stringWrapper(iter.next().str()));
    }
	if (data.exactly_phrases.empty()) (data.exactly_phrases).insert("abcde"); // при отсутствии точных фраз в индекс заносится фраза =abcde=

	//Заполнение минус слов
	//----------------------------------------------------------------------------------------------------------------------------
	iter = x.getObjectField("minus_words");
	data.minus_words.clear();
	while (iter.more()) {
		(data.minus_words).insert(iter.next().str());
    	}
	if (data.minus_words.empty()) (data.minus_words).insert("abcde"); // при отсутствии минус слов в индекс заносится фраза =abcde=

	//Заполнение списка информеров, закоторыми закреплено рекламное предложение
	//----------------------------------------------------------------------------------------------------------------------------	
	iter = x.getObjectField("listAds");
	data.informer_ids.clear();
	while (iter.more()) {
		(data.informer_ids).insert(iter.next().str());
    	}

	//Заполнение списка тематик, закоторым удовлетворяет рекламное предложение
	//----------------------------------------------------------------------------------------------------------------------------	
	iter = x.getObjectField("topics");
	data.topic_ids.clear();
	while (iter.more()) {
		(data.topic_ids).insert(iter.next().str());
    	}
	if (data.topic_ids.empty()) (data.topic_ids).insert("common"); // при отсутствии тематик в индекс заносится фраза =common=
		
		
	//Добавление документа в индекс
	addDocumentToModifierWriter(indexModifier, data);
	
	} // while
	
	indexModifier->flush();
	indexModifier->optimize();
	indexModifier->close();
	_CLLDELETE(indexModifier);
	LOG(INFO)<<"Модификация индекса завершена";
	delete analyzer;
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

	//LOG(INFO)<<"queue = "<<queue<<"   command="<<command<<endl;
	//printf("%s %s\n",queue.c_str(), command.c_str());




	
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
	
    
	while (cursor->more()) {

	
		mongo::BSONObj x = cursor->next();
		data.informer = x.getStringField("guid");
				//LOG(INFO) << "informer:"<<data.informer;

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

			addDocumentToModifierWriterNew(indexModifier, data);
			
		}
  		

	} // while

	//LOG(INFO) << "Loaded " << count << " accordings";

	
	
	indexModifier->flush();
	indexModifier->optimize();
	indexModifier->close();
	_CLLDELETE(indexModifier);
	LOG(INFO)<<"Модификация индекса завершена";
	delete analyzer;
}

/**
	\brief Метод поиска в построенном индексе. 
	
	Метод используется для тестирования.
*/
void Core::SearchFiles(const char* index){
    //standard::StandardAnalyzer analyzer;
const TCHAR* stopWords[] = {
    _T("компьютер"), _T("ноутбук") 
  };

lucene::analysis::snowball::SnowballAnalyzer analyzer(_T("Russian"), stopWords );
    char line[80];
    TCHAR tline[80];
    TCHAR* buf;

    IndexReader* reader = IndexReader::open(index);
    while (true) {
        printf("Enter query string: ");
        char* tmp = fgets(line,80,stdin);
        if ( tmp == NULL ) continue;
        line[strlen(line)-1]=0;

        IndexReader* newreader = reader->reopen();
        if ( newreader != reader ){
            _CLLDELETE(reader);
            reader = newreader;
        }
        IndexSearcher s(reader);

        if ( strlen(line) == 0 )
            break;
        lucene_utf8towcs(tline,line,80);
        Query* q = QueryParser::parse(tline,_T("keywords"),&analyzer);

        buf = q->toString(_T("keywords"));
        _tprintf(_T("Searching for: %s\n\n"), buf);
        _CLDELETE_LCARRAY(buf);

        uint64_t str = Misc::currentTimeMillis();
        Hits* h = s.search(q);
        uint32_t srch = (int32_t)(Misc::currentTimeMillis() - str);
        str = Misc::currentTimeMillis();
	
	_tprintf(_T("Result - %d\n"), h->length());

        for ( size_t i=0;i<h->length();i++ ){
            Document* doc = &h->doc(i);
            //const TCHAR* buf = doc.get(_T("contents"));
            _tprintf(_T("%d. %s - %f  (%s)\n"), i, doc->get(_T("guid")), h->score(i), doc->get(_T("title")));
        }

        printf("\n\nSearch took: %d ms.\n", srch);
        printf("Screen dump took: %d ms.\n\n", (int32_t)(Misc::currentTimeMillis() - str));

        _CLLDELETE(h);
        _CLLDELETE(q);

        s.close();
    }
    reader->close();
    _CLLDELETE(reader);
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
    	try {


		LOG(INFO)<<"Creating object AMQP...  ";
		amqp_ = new AMQP;
		LOG(INFO)<<"Creating exchange... ";
		exchange_ = amqp_->createExchange();
		LOG(INFO)<<"Declaring exchange... ";
		exchange_->Declare("indexator", "topic", AMQP_AUTODELETE);
		break;
 	    } catch (AMQPException &ex) {
		LOG(INFO) << "Error in exchange init: " + ex.getMessage();
		delete amqp_;
		not_init++;
		sleep(30);
    	    }
	}

	if (not_init==100) return;
	else LOG(INFO) << "Exchange was declared succesfully!!! ";


	try {
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

	//exchange_->Publish("Offer:a6c46c1a-3612-4157-ae57-a2014567ee70;Campaign:31a1534a-cced-4587-ad30-7c1bd805db6a", "advertise.delete");
	//exchange_->Publish("Offer:a6c46c1a-3612-4157-ae57-a2014567ee70;Campaign:31a1534a-cced-4587-ad30-7c1bd805db6a", "advertise.update");
	//exchange_->Publish("6aa5383e-5ddb-4eb5-b693-d96acd17409b", "campaign.delete");
	//exchange_->Publish("Offer:bbbbbbbbbbbbb-3612-4157-ae57-a2014567ee70;Campaign:31a1534a-cced-4587-ad30-7c1bd805db6a", "advertise.update");
	//exchange_->Publish("Offer:bbbbbbbbbbbbb-3612-4157-ae57-a2014567ee70;Campaign:31a1534a-cced-4587-ad30-7c1bd805db6a", "advertise.update");
	//exchange_->Publish("Offer:bbbbbbbbbbbbb-3612-4157-ae57-a2014567ee70;Campaign:31a1534a-cced-4587-ad30-7c1bd805db6a", "advertise.update");
	//exchange_->Publish("6aa5383e-5ddb-4eb5-b693-d96acd17409b", "campaign.delete");
	//exchange_->Publish("6aa5383e-5ddb-4eb5-b693-d96acd17409b", "campaign.update");
	//exchange_->Publish("3a14c42a-2fa7-11e0-a734-00163e0300c1", "informer_rating.update");
	//exchange_->Publish("3a14c42a-2fa7-11e0-a734-00163e0300c1", "informer_rating.delete");
	



    } catch (AMQPException &ex) {
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
	
	Используется при добавлении списка ключевых слов в поле индекса.
*/

TCHAR* Core::stringUnion (const std::set<std::string> &myset)
{
	std::string temp;
	StringBuffer str;
	TCHAR * tf = new TCHAR[CL_MAX_DIR];
    	char * f = new char [CL_MAX_DIR];

	strcpy(f,"");

	set<string>::iterator it;

//LOG(INFO)<<"size = "<<myset.size();
for ( it=myset.begin() ; it != myset.end(); it++ )
	{
		string t = *it;
		boost::trim(t);
		if ((strlen(f) + strlen(t.c_str())) >CL_MAX_DIR-1) {/*LOG(ERROR)<<"Too big";*/ break;}
		
		strcat(f,t.c_str());
		strcat(f," ");
		//LOG(INFO)<<"v = "<<(*it).c_str()<<" =";
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
	\brief Преобразование строки к виду $строка$. 
	
	Используется при добавлении "точных фраз" 
*/
string Core::stringWrapper(const string &str)
{
	string t = str;
	boost::trim(t);
	return ("$"+t+"$");
}

string Core::to_string(const float& value)
{
//stringstream oss;
//oss << value;
//return oss.str();
char buf[18]; // все равно максимальная точность на Intel платформе 17 знаков
sprintf(buf,"%17.2f",value);
string t(buf);
boost::trim(t);
return t;
}

string Core::to_string1(const float& value)
{

char buf[18]; // все равно максимальная точность на Intel платформе 17 знаков
sprintf(buf,"%17.0f",value);
string t(buf);
boost::trim(t);
//stringstream oss;
//oss << value;
//string t = oss.str();
int k = 25 - t.size();
t.insert(t.begin(), k, '0');
return t;
}
/*
string Core::to_string(const float& value)
{
stringstream oss;
oss << value;
return oss.str();
}

string Core::to_string1(const float& value)
{
stringstream oss;
oss << value;
string t = oss.str();
int k = 25 - t.size();
t.insert(t.begin(), k, '0');
return t;
}

*/

