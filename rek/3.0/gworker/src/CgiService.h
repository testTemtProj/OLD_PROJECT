#ifndef CGISERVICE_H
#define CGISERVICE_H

#include <string>

class Core;

class CgiService {

public:
    /** Инициализирует сервис.
     *
     * Читает настройки из переменных окружения.
     *
     * Реально подключения к базам данных, RabbitMQ и другому происходит
     * при первом запросе в методе Serve().
     */
    CgiService(int argc, char *argv[]);
    ~CgiService();

    /** Начало обработки поступающих от FastCgi (или CGI) сервера запросов.
     *
     * Если запущен CGI сервером или просто из командной строки, то обработает
     * один запрос и вернёт управление.
     *
     * Если запущен FastCgi сервером, то будет ждать и обрабатывать следующие
     * запросы.
     */
    void Serve();

private:
    /** Возвращает ответ FastCgi серверу.
     *
     * \param out       указатель на строку ответа.
     * \param status    HTTP статус ответа (например, 200, 404 или 500).
     * \param content_type Заголовок "Content-Type".
     */
    void Response(const char *out, int status,
		  const char *content_type = "text/html");

    /** Возвращает ответ FastCgi серверу.
     *
     * \param out       строка ответа.
     * \param status    HTTP статус ответа (например, 200, 404 или 500).
     * \param content_type Заголовок "Content-Type".
     */
    void Response(const std::string &out, int status,
		  const char *content_type = "text/html");

    /** Создаёт подключения к базам данных.
     *
     * Настройки читаются конструктором класса из переменных окружения среды.*/
    bool ConnectDatabase();

    /** Возвращает значение переменной окружения name или default_value,
     *  если значение не установлено.
     *
     *  \param name     переменная окружения.
     *  \param default_value значение по умолчанию.*/
    std::string getenv(const char *name, const char *default_value);

    char *getenv(const char *name) { return ::getenv(name); }

    /** Обработка одного запроса.
     *
     * \param query     строка запроса (всё, что начинается после
     *                  вопросительного знака в URL запроса).
     * \param ip        IP посетителя, сделавшего запрос.
     * \param script_name название скрипта (то, что идёт до вопросительного
     *                  знака). Необходимо получать это значение от веб-сервера,
     *                  поскольку может меняться в зависимости от настроек
     *                  FastCGI. Используется для построения ссылки на новую
     *                  порцию предложений.
     */
    void ProcessRequest(const std::string &query,
			const std::string &ip,
			const std::string script_name);

private:

    int argc;
    char **argv;

    /** Указатель на экземпляр ядра службы, который занимается реальной
     * обработкой запросов. */
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


    /// \name Параметры подключения к базе данных журнала
    ///@{
    /** Адрес сервера баз данных. */
    std::string mongo_log_host_;

    /** Название базы данных. */
    std::string mongo_log_db_;

    /** Название группы реплик (если база данных находится в Replica Set). */
    std::string mongo_log_set_;

    /** Может ли сервис подключаться к slave серверам базам данных.
     *  Это балансирует нагрузку в режиме только для чтения, но появляется
     *  вероятность чтения не самых свежих данных (разница от мастера до
     *  нескольких секунд).
     */
    bool mongo_log_slave_ok_;
    ///@}

    /// \name Другие параметры сервера
    ///@{
    /** IP сервера. Ссылка на редирект по рекламному предложению содержит в
     *  себе адрес сервера, который её создал. */
    std::string server_ip_;

    /** Название скрипта обработки редиректа. */
    std::string redirect_script_;

    ///@}
};

#endif
