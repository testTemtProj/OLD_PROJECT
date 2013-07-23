#ifndef INDEXCREATORSERVICE_H
#define INDEXCREATORSERVICE_H

#include <string>

class Core;

/** 
 * Этот класс отвечает за подключение к базе данных рекламных предложений
 * и запуск ядра приложения.
 *
 * \see Serve().
 */
class IndexCreatorService {

public:
    /** Инициализирует сервис.
     *

     */
    IndexCreatorService (std::string fileName);
    ~IndexCreatorService ();

void InitDefault();
void InitDBs(std::string fileName);

    /** Запус ядра при условии удачного подключения к БД.
     */
    int Serve();

private:
 

    /** Создаёт подключения к базам данных.
     *
     * Настройки читаются конструктором класса из файла.*/
    bool ConnectDatabase();

   

private:

    int argc;
    char **argv;

    /** Указатель на экземпляр ядра, который занимается построением и обновлением индекса. */
    Core *core;

    /// \name Параметры подключения к основной базе данных.
    ///@{
    /** Адрес сервера баз данных. */
    std::string mongo_main_host_;

    /** Название базы данных. */
    std::string mongo_main_db_;

    /** Название группы реплик (если база данных находится в Replica Set). */
    std::string mongo_main_set_;

    /** Может ли сервис подключаться к slave серверам базам данных.
     *  Это балансирует нагрузку в режиме только для чтения, но появляется
     *  вероятность чтения не самых свежих данных (разница от мастера до
     *  нескольких секунд).
     */
    bool mongo_main_slave_ok_;
	 ///@}
	 
	/// \name Параметры индексирования
    ///@{
	/**
	* Имя папки, в которую будет сохранен построенный индекс
	*/
    std::string index_folder_offer_;
    ///@}
	std::string index_folder_informer_;

 };

#endif
