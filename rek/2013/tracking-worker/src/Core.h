#ifndef CORE_H
#define CORE_H

#include <list>
#include <vector>
#include <map>
#include <utility>
#include <boost/date_time.hpp>
#include <boost/algorithm/string.hpp>

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
     * - При необходимости создаёт локальную базу данных MongoDB с нужными
     *   параметрами.
     */
    Core();

    /** При работе с FastCGI
     *  никогда не вызывается (как правило, процессы просто снимаются).
     */
    ~Core();
    /** \brief  Обработка запроса.
     *
     * \param params    Параметры запроса.
     */
    std::string Process(const Params &params);
    std::string stringWrapper(const std::string &str, bool replaceNumbers = false);
    /** \brief  Увеличивает счётчики показов предложений ``items`` */
    void markAsShown(const Params &params);

    /** \brief  Выводит состояние службы и некоторую статистику */
    std::string Status();

    /** \brief  Возвращает HTML */
    std::string OffersToHtml() const;

private:
    void InitMongoDB();
	/// Счётчик обработанных запросов
    static int request_processed_; 

	/// Время запуска службы
    boost::posix_time::ptime time_service_started_; 

	/// Время начала последнего запроса
    boost::posix_time::ptime time_request_started_; 
};


#endif // CORE_H
