#ifndef CORE_H
#define CORE_H

#include <list>
#include <vector>
#include <map>
#include <utility>
#include <boost/date_time.hpp>
#include <boost/algorithm/string.hpp>
#include <boost/foreach.hpp>
#include <boost/date_time/posix_time/ptime.hpp>
#include <boost/date_time/posix_time/posix_time_io.hpp>
#include <boost/format.hpp>
#include <glog/logging.h>
#include <ctime>
#include <cstdlib>
#include <sstream>
#include <time.h>
#include <fstream>
#include <mongo/util/version.h>
#include <amqpcpp.h>

#include <CLucene.h>
#include <CLucene/StdHeader.h>
#include <CLucene/_clucene-config.h>
#include <CLucene/util/CLStreams.h>
#include <CLucene/util/dirent.h>
#include <CLucene/config/repl_tchar.h>
#include <CLucene/config/repl_wchar.h>
#include <CLucene/util/Misc.h>
#include <CLucene/util/StringBuffer.h>
#include <CLucene/config/repl_wctype.h>
#include "CLucene/index/IndexModifier.h"
#define _UNICODE

#include "DB.h"
#include "Offer.h"


using namespace lucene::index;
using namespace lucene::analysis;
using namespace lucene::util;
using namespace lucene::store;
using namespace lucene::document;
using namespace lucene::search;
using namespace lucene::queryParser;


/// Класс, являющийся ядром системы
class Core
{
public:


    /** \brief  Создаёт ядро.
     *
     * 
     *
     */
    Core(const std::string &index_folder_offer, const std::string &index_folder_informer);

    /** Пытается красиво закрыть очереди RabbitMQ.
     */
    ~Core();

    /** \brief  Запускает приложение в бесконечный цикл.
     *
     */
    int Process();


    /** \brief  Производит построение индекса. */
    void CreateIndexForOffers(const bool clearIndex);
	void CreateIndexForInformers(const bool clearIndex);
	
	/** \brief  Создаёт документ для индекса. */
	void createOfferDocument(Document &doc, OfferKeywordsData &offer);
	void createRatingDocument(Document &doc, OfferInformerRating &data);
	

	/** \brief  Обновление индекса */
	void ModifyOfferIndex(std::string offer_guid, std::string command);
	void ModifyInformerIndex(std::string offer_guid, std::string command);
	
 
    /** \brief  Обрабатывает новые сообщения в очереди RabbitMQ. */
    bool ProcessMQ();

	Document doc;

 private:
    /** \brief  Инициализация очереди сообщений */
    void InitMessageQueue();
    
    /** \brief  Логирование сообщений  AMQP*/
    void LogToAmqp(const std::string &message);
	
	/** \brief  Объединение строк в одну строку. Используется для объединения в одну строку множества ключевых слов.*/
	TCHAR* stringUnion (const std::set<std::string> &myset);
	
	/** \brief  Перевод символов строки в нижний регистр. Используется при построении индекса.*/
	void _tCharToLow (TCHAR* str);
	
	/** \brief  Перевод в строку.*/
	string to_string(const float& value);
	string to_string(const bool& value);
    string exec();

    
    bool amqp_initialized_;
    bool amqp_down_;
    AMQP *amqp_;
    AMQPExchange *exchange_;                        /// Точка обмена
    AMQPQueue *mq_campaign_;                        /// Очередь сообщений об изменениях в кампаниях
    AMQPQueue *mq_advertise_;                       /// Очередь сообщений об изменениях в рекламных предложениях
    AMQPQueue *mq_account_;                         /// Очередь сообщений об изменениях в аккаунтах
	AMQPQueue *mq_informer_;                        /// Очередь сообщений об изменениях в информерах
    std::vector<std::string> mq_log_;               /// История полученных сообщений MQ

    static int request_processed_;                  /// Счётчик обработанных запросов
    boost::posix_time::ptime time_service_started_; /// Время запуска службы
    boost::posix_time::ptime time_last_mq_check_;   /// Время последней проверки MQ
    boost::posix_time::ptime time_request_started_; /// Время начала последнего запроса

	std::string index_folder_offer_;                /// Папка, в которую построится индекс
	std::string index_folder_informer_;             /// Папка, в которую построится индекс
};
#endif // CORE_H
