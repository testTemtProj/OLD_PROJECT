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
public:
    enum ShowNonRelevant {
	Show_Social,
	Show_UserCode
    };

private:
    struct InformerData {
	InformerData(std::string &id)
	    : id(id), blocked(false), nonrelevant(Informer::Show_Social),
	    capacity(0), valid(false) { }
	std::string id;
	std::string title;
	std::string teasersCss;//изменено RealInvest Soft
	std::string domain;
	std::string user;
	bool blocked;
	std::set<std::string> categories;
	ShowNonRelevant nonrelevant;
	std::string user_code;
	int capacity;
	bool valid;



	/** поля, добавленные RealInvest Soft*/
	int height;
	int width;
	std::string bannersCss;

    };

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
	    assert( inf2.valid() == true );	// Если информер существует, или
	    assert( inf2.valid() == false );	// Если информер не существует
						// или не был загружен
    */
    bool is_null() const { return d->id.empty(); }

    std::string id() const	  {return d->id; }
    std::string title() const	  {return d->title; }
	/** css для тизеров */
    std::string teasersCss() const	  {return d->teasersCss; }
	/** css для баннеров */
	std::string bannersCss() const	  {return d->bannersCss; }
    std::string domain() const	  {return d->domain; }
    std::string user() const	  {return d->user; }
    bool blocked() const	  {return d->blocked; }
    ShowNonRelevant nonrelevant() const {return d->nonrelevant; }
    std::string user_code() const {return d->user_code; }
    const std::set<std::string> &categories() const {return d->categories; }

    /** Количество предложений, которое может вместить информер */
    int capacity() const	  {return d->capacity; }



	/** методы, добавленные RealInvest Soft*/
	/** высота рекламного блока (используется для проверки размеров баннеров) */
	int height() const { return d->height; }
	/** ширина рекламного блока (используется для проверки размеров баннеров) */
	int width() const { return d->width; }







    bool operator==(const Informer &other) const;
    bool operator<(const Informer &other) const;

private:
    InformerData *d;

    static std::map<std::string, Informer::InformerData*> informer_data_by_id_;

    static void LoadCategoriesByDomain(std::set<std::string> &categories,
				       const std::string &domain);
    static std::set<std::string> GetBlockedAccounts();
    static bool _loadFromQuery(const mongo::Query &query);
};

#endif // INFORMER_H
