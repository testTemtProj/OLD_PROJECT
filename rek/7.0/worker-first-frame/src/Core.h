#ifndef CORE_H
#define CORE_H

#include <list>
#include <vector>
#include <map>
#include <utility>
#include <string>
#include <boost/date_time.hpp>
#include <boost/algorithm/string.hpp>
#include <amqpcpp.h>

#include "Informer.h"
#include "Params.h"


/// Класс, который связывает воедино все части системы.
class Core
{
public:
    /** \brief  Создаёт ядро.
     *
     * Производит все необходимые инициализации:
     *
     * - Загружает все сущности из базы данных;
     * - Подключается к RabbitMQ и создаёт очереди сообщений;
     * - При необходимости создаёт локальную базу данных MongoDB с нужными
     *   параметрами.
     */
    Core();

    /** Пытается красиво закрыть очереди RabbitMQ, но при работе с FastCGI
     *  никогда не вызывается (как правило, процессы просто снимаются).
     */
    ~Core();

    /** \brief  Обработка запроса на показ рекламы.
     *
     * Самый главный метод. Возвращает HTML-строку, которую нужно вернуть
     * пользователю.
     *
     * Пример вызова:
     *
     * \Example
     * \code
     * Core core(Params().ip("192.168.0.1")
     *                         .informer("informer#01"));
     * \endcode
     *
     * \param params    Параметры запроса.
     */
    std::string Process(const Params &params);


    /** \brief  Загружает все сущности, которые используются при показе
     *          рекламы. */
    void LoadAllEntities();
    

    /** \brief  Обрабатывает новые сообщения в очереди RabbitMQ. */
    bool ProcessMQ();


    /** \brief  Выводит состояние службы и некоторую статистику */
    std::string Status();


    /** \brief  IP сервера, на котором запущена служба */
    std::string server_ip() const { return server_ip_; }
    void set_server_ip(const std::string &ip) {
	server_ip_ = ip;
    }

private:
    void InitMessageQueue();
    std::string RequestDebugInfo(const Params &params) const;
    void LogToAmqp(const std::string &message);
    std::string frame_html;
    std::string frame_query;
    bool amqp_initialized_;
    bool amqp_down_;
    AMQP *amqp_;
	
	/// Точка обмена
    AMQPExchange *exchange_;  
	
	/// Очередь сообщений об изменениях в информерах
    AMQPQueue *mq_informer_; 
	
	/// Очередь сообщений об изменениях в аккаунтах
    AMQPQueue *mq_account_;  
	
	/// История полученных сообщений MQ
    std::vector<std::string> mq_log_; 

	/// Счётчик обработанных запросов
    static int request_processed_; 

	static int offer_processed_;

	static int social_processed_;
	
	/// Время запуска службы
    boost::posix_time::ptime time_service_started_; 
	
	/// Время последней проверки MQ
    boost::posix_time::ptime time_last_mq_check_;   
	
	/// Время начала последнего запроса
    boost::posix_time::ptime time_request_started_; 

	///Адрес сервера
    std::string server_ip_;
};


#endif // CORE_H
