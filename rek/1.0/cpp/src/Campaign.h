#ifndef CAMPAIGN_H
#define CAMPAIGN_H

#include <string>
#include <map>
#include <list>

/** \brief Класс, описывающий рекламную кампанию.
*/
class Campaign
{
    /** Структура для хранения данных о рекламной кампании. */
    struct CampaignData {
        CampaignData(const std::string &id) :
	        id(id), social(false), valid(false) { }
        std::string id;         ///< ID кампании.
        std::string title;      ///< Заголовок кампании.
        bool social;            ///< Является ли реклама социальной.
        bool valid;             ///< Запись действительна.
    };

public:
    Campaign(const std::string &id);

    /** \brief  Загружает информацию обо всех кампаниях */
    static void loadAll();

    /** \brief  ID кампании */
    std::string id() const { return d->id; }

    /** \brief  Название кампании */
    std::string title() const { return d->title; }

    /** \brief  Является ли кампания социальной.

	Переходы по социальной рекламе не засчитываются владельцам сайтов.
	Социальная реклама показывается в том случае, если при данных условиях
	(страна, время и т.д.) больше нечего показать.

	По умолчанию равно false (кампания является коммерческой).
      */
    bool social() const { return d->social; }

    /** \brief  Возвращает true, если кампания действительна (была успешно загружена) */
    bool valid() const { return d->valid; }

    /** \brief  Список всех кампаний */
    static std::list<Campaign> &all() {
	static std::list<Campaign> all_;
	return all_;
    }


    bool operator==(const Campaign &other) const {
	return this->d == other.d;
    }
    bool operator<(const Campaign &other) const {
	return this->d < other.d;
    }

private:
    CampaignData *d;

    static std::map<std::string, CampaignData*> &cache() {
	static std::map<std::string, CampaignData*> cache_;
	return cache_;
    }


};

#endif // CAMPAIGN_H
