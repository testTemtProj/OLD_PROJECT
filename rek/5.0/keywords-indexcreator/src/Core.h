#ifndef CORE_H
#define CORE_H

#include <list>
#include <vector>
#include <map>
#include <utility>
#include <boost/date_time.hpp>
#include <boost/algorithm/string.hpp>
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
#include <CLucene/snowball/SnowballAnalyzer.h>
#define _UNICODE


using namespace lucene::index;
using namespace lucene::analysis;
using namespace lucene::util;
using namespace lucene::store;
using namespace lucene::document;
using namespace lucene::search;
using namespace lucene::queryParser;


#include "OfferKeywords.h"

/// Класс, являющийся ядром системы
class Core
{
public:


    /** \brief  Создаёт ядро.
     *
     * 
     *
     */
    Core(const std::string &index_folder_offer, const std::string &index_folder_informer, const std::string &stop_words);

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
	
	/** \brief  Добавляет документ в индекс. */
	void addDocumentToWriter( IndexWriter* writer, OfferKeywordsData &offer);
	void addDocumentToWriterNew( IndexWriter* writer, OfferInformerRating &data);
	
	/** \brief  Добавляет документ в индекс при модификации */
	void addDocumentToModifierWriter( IndexModifier* writer, OfferKeywordsData &offer);
	void addDocumentToModifierWriterNew( IndexModifier* writer, OfferInformerRating &data);
	

	/** \brief  Обновление индекса */
	void ModifyOfferIndex(std::string offer_guid, std::string command);
	void ModifyInformerIndex(std::string offer_guid, std::string command);
	
	/** \brief  Поиск по индексу (используется для тестирования)*/
	void SearchFiles(const char* index);
    
 
    /** \brief  Обрабатывает новые сообщения в очереди RabbitMQ. */
    bool ProcessMQ();

	Document doc;
    const TCHAR** array_stop_words;                /// Массив стоп слов
    static const TCHAR* stop_Words[];

 private:
    /** \brief  Инициализация очереди сообщений */
    void InitMessageQueue();
    
    /** \brief  Логирование сообщений  AMQP*/
    void LogToAmqp(const std::string &message);
	
	/** \brief  Объединение строк в одну строку. Используется для объединения в одну строку множества ключевых слов.*/
	TCHAR* stringUnion (const std::set<std::string> &myset);
	
	/** \brief  Перевод символов строки в нижний регистр. Используется при построении индекса.*/
	void _tCharToLow (TCHAR* str);
	
	/** \brief  Преображование строки, добавлением в начало и в конец символа $. Используется для разметки точных фраз. */
	string stringWrapper(const string &str);
	string to_string(const float& value);
	string to_string1(const float& value);
    /* * \brief  Нормализирует строку. Уберает знаки припенания, лишнии пробелы и цифры если необходимо*/
    string stringNormalizer(const string &str, bool replaceNumbers = false);
    

    
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
    std::string stop_words_;                        /// Файл стоп-слов
};
#endif // CORE_H
