#ifndef INFORMER_H
#define INFORMER_H

#include <string>
#include <map>
#include <set>


// Forward declarations
namespace mongo { class Query; }

/**
    \brief Класс, описывающий рекламную выгрузку
*/
class Informer
{
private:
    struct InformerData {
	InformerData(std::string &id): id(id), blocked(false), valid(false) { }
	std::string id;                         //Индентификатор РБ
	std::string domain;                     //Доменное имя за которым заркеплён РБ
	std::string user;                       //Логин аккаунта Getmyad за которым заркеплён РБ
	std::string title;                      //Название РБ
	bool blocked;                           //Статус активности РБ
	bool valid;                             //Валидность блока
	int height;                             //Высота блока
	int width;                              //Ширина блока
    };
    InformerData *d;
    static std::map<std::string, Informer::InformerData*> informer_data_by_id_;
    static std::set<std::string> GetBlockedAccounts();
    static bool _loadFromQuery(const mongo::Query &query);

public:
    Informer(std::string id = "");

    /** Загружает информацию обо всех информерах */
    static bool loadAll();

    /** Перезагружает информер \a informer */
    static bool loadInformer(const Informer &informer);

    /** Помечает все информеры как невалидные */
    static void invalidateAll();

    /** Возвращает true, если информер действителен.
	Действительным считается информер, который был найден и загружен из
	базы данных.
    */
    bool valid() const { return d->valid; }

    /** Возвращает true, если информер нулевой.
	Нулевой информер -- это информер, который не имеет id. Например:
	    Informer inf1;
	    assert( inf1.null() == true );
	    assert( inf1.valid() == false );

	    Informer inf2("INF");
	    assert( inf2.null() == false );
	    assert( inf2.valid() == true );      // Если информер существует
	    assert( inf2.valid() == false );	// Если информер не существует или не был загружен
    */
    bool is_null() const { return d->id.empty(); }

    std::string id() const	  {return d->id; }
    std::string title() const	  {return d->title; }
    std::string domain() const	  {return d->domain; }
    std::string user() const	  {return d->user; }
    bool blocked() const	  {return d->blocked; }
	/** высота рекламного блока */
	int height() const { return d->height; }
	/** ширина рекламного блока */
	int width() const { return d->width; }
    bool operator==(const Informer &other) const;
    bool operator<(const Informer &other) const;
};

#endif // INFORMER_H
