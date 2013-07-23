#ifndef INFORMER_H
#define INFORMER_H

#include <string>
#include <map>
#include <set>


// Forward declarations
namespace mongo { class Query; }

/** \brief Класс, описывающий рекламную выгрузку
*/
class Informer
{
public:
    /** Действие при отсутствии релевантной рекламы */
    enum ShowNonRelevant {
        Show_Social,        /**< показывать социальную рекламу */
        Show_UserCode       /**< показывать пользовательский код */
    };

private:

    /** Структура для хранения данных об информере. */
    struct InformerData {
        InformerData(std::string &id)
	        : id(id), blocked(false), nonrelevant(Informer::Show_Social),
	        capacity(0), valid(false) { }
        std::string id;         ///< ID
        std::string title;      ///< Наименование информера
        std::string css;        ///< CSS стиль информера
        std::string domain;     ///< Домен, к которому принадлежит информер
        std::string user;       ///< Пользователь, которому принадлежит информер
        bool blocked;           ///< Заблокирован ли информер
        std::set<std::string> categories;   ///< Множество категорий, к которым относится информер
        ShowNonRelevant nonrelevant;    ///< Действие при отстутсвии релевантной рекламы
        std::string user_code;
        int capacity;           ///< Количество предложений на информере
        bool valid;             ///< Действительна ли запись
    };

public:
    Informer(std::string id = "");

    /** \brief  Загружает информацию обо всех информерах */
    static bool loadAll();

    /** \brief  Перезагружает информер \a informer */
    static bool loadInformer(const Informer &informer);

    /** \brief  Помечает все информеры как невалидные */
    static void invalidateAll();

    /** \brief Возвращает true, если информер действителен.

	Действительным считается информер, который был найден и загружен из
	базы данных.
    */
    bool valid() const { return d->valid; }

    /** \brief  Возвращает true, если информер нулевой.

	Нулевой информер -- это информер, который не имеет id. Например:

        \code
	    Informer inf1;
	    assert( inf1.null() == true );
	    assert( inf1.valid() == false );

	    Informer inf2("INF");
	    assert( inf2.null() == false );
	    assert( inf2.valid() == true );	// Если информер существует, или
	    assert( inf2.valid() == false );	// Если информер не существует
						// или не был загружен
        \endcode
    */
    bool is_null() const { return d->id.empty(); }

    /// ID информера.
    std::string id() const	  {return d->id; }

    /// Наименование информера.
    std::string title() const	  {return d->title; }

    /// CSS стиль информера.
    std::string css() const	  {return d->css; }

    /// Домен, к которому привязан информер.
    std::string domain() const	  {return d->domain; }

    /// Пользователь, которому принадлежит информер.
    std::string user() const	  {return d->user; }

    /// Является ли информер заблокированым.
    bool blocked() const	  {return d->blocked; }

    /// Действие при отсутствии релевантной рекламы.
    ShowNonRelevant nonrelevant() const {return d->nonrelevant; }

    /// Пользовательский код, который выводится при отсутствии релевантной
    /// рекламы (если nonrelevant() == true).
    std::string user_code() const {return d->user_code; }

    /// Множество категорий, к которым относится информер.
    const std::set<std::string> &categories() const {return d->categories; }

    /// Количество предложений, которое может вместить информер.
    int capacity() const	  {return d->capacity; }

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
