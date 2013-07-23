#ifndef CAMPAIGN_H
#define CAMPAIGN_H

#include <string>
#include <map>
#include <list>


/**
  \brief  Класс, описывающий рекламную кампанию
*/
class Campaign
{
    struct CampaignData {
	CampaignData(const std::string &id) :
		id(id), social(false), valid(false) { }

	///идентификатор рекламной кампании	
	std::string id;			

	///название рекламной кампании
	std::string title;	
	
	///признак, является ли кампания социальной
	bool social;	

	///признак успешной загрузки кампании
	bool valid;				
    };

public:
    Campaign(const std::string &id);

    /** \brief Загружает информацию обо всех кампаниях */
    static void loadAll();

    /** \brief Возвращает идентификатор рекламной кампании */
    std::string id() const { return d->id; }

    /** \brief Возвращает название рекламной кампании */
    std::string title() const { return d->title; }

    /** \brief Является ли кампания социальной.

	Переходы по социальной рекламе не засчитываются владельцам сайтов.
	Социальная реклама показывается в том случае, если при данных условиях
	(страна, время и т.д.) больше нечего показать.

	По умолчанию равно false (кампания является коммерческой).
      */
    bool social() const { return d->social; }

    /** \brief Возвращает true, если кампания действительна (была успешно загружена) */
    bool valid() const { return d->valid; }

    /** \brief Возвращает список всех кампаний */
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
