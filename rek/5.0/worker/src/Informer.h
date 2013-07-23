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
	std::string id;                         //Индентификатор РБ
	std::string title;                      //Название РБ
	std::string teasersCss;                 //Стиль CSS РБ для отображения тизеров
	std::string bannersCss;                 //Стиль CSS РБ для отображения банеров
	std::string domain;                     //Доменное имя за которым заркеплён РБ
	std::string user;                       //Логин аккаунта Getmyad за которым заркеплён РБ
	bool blocked;                           //Статус активности РБ
	std::set<std::string> categories;       //Принадлежность РБ к категории
	ShowNonRelevant nonrelevant;            //Что отображать при отсутствии платных РП
	std::string user_code;                  //Строка пользовательского кода
	int capacity;                           //Количество мест под тизер
	bool valid;                             //Валидность блока
	int height;                             //Высота блока
	int width;                              //Ширина блока
    int height_banner;                      //Высота отображаемых банеров
    int width_banner;                       //Ширина отображаемых банеров

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
	    assert( inf2.valid() == true );      // Если информер существует
	    assert( inf2.valid() == false );	// Если информер не существует или не был загружен
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
	/** высота рекламного блока (используется для проверки отображаемой области) */
	int height() const { return d->height; }
	/** ширина рекламного блока (используется для проверки отображаемой области) */
	int width() const { return d->width; }
	/** высота возможно отображаемого банера (используется для проверки возможно ли здесь отобразить банер) */
	int height_banner() const { return d->height_banner; }
	/** ширина возможно отображаемого банера (используется для проверки возможно ли здесь отобразить банер) */
	int width_banner() const { return d->width_banner; }
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
