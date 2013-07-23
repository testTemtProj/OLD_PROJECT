#ifndef CAMPAIGNSHOWOPTIONS_H
#define CAMPAIGNSHOWOPTIONS_H

#include <string>
#include <list>
#include <set>
#include <map>
#include <boost/date_time.hpp>

#include "Campaign.h"
#include "Informer.h"


/** \brief  Класс описывает на каких информерах и при каких условиях показывать
  *         рекламную кампанию */
class CampaignShowOptions
{
public:
    CampaignShowOptions(Campaign c);

    /// Покрытие рекламных площадок:
    enum ShowCoverage {
        /** кампания будет показана везде, кроме элементов, перечисленных в
         *  ignored. */
        Show_All,       

        /** кампания будет показана на доменах, совпадающих по тематике
         *  (категориям). Из просмотра исключаются ignored элементы и
         *  добавляются allowed. */
        Show_Thematic,

        /** кампания будет показываться только на allowed
         *  информерах/аккаунтах/доменах. */
        Show_Allowed
    };


    Campaign campaign() const { return campaign_; }

    /** \brief  Множество стран, на которых будет отображатся кампания.

	Каждая страна представлена двухбуквенным кодом (например, RU - Россия,
	UA - Украина и т.д.

	Факт, что кампания должна показываться во всех странах, отражается
	пустым множеством.
      */
    std::set<std::string> country_targeting() const {
	return country_targeting_;
    }

    /** \brief  Множество областей, в которых должна отображаться кампания.

	Название области должно соответствовать написанию, принятому в базе
	MaxMind GeoLite City (например, "Kharkivs'ka Oblast'").

	Выключенный таргетинг по городам обозначается пустым множеством.
    */
    std::set<std::string> region_targeting() const { return region_targeting_; }

    /** \brief  Множество информеров, на которых можно показывать кампанию */
    std::set<Informer> allowed_informers() const { return allowed_informers_; }

    /** \brief  Множество аккаунтов getmyad, которым можно показывать кампанию */
    std::set<std::string> allowed_accounts() const { return allowed_accounts_; }

    /** \brief  Множество доменов, на которых можно показывать кампанию */
    std::set<std::string> allowed_domains() const { return allowed_domains_; }

    /** \brief  Множество информеров, на которых НЕ нужно показывать кампанию */
    std::set<Informer> ignored_informers() const { return ignored_informers_; }

    /** \brief  Множество доменов, на которых НЕ нужно показывать кампанию */
    std::set<std::string> ignored_domains() const { return ignored_domains_; }

    /** \brief  Множество аккаунтов GetMyAd, на которых НЕ нужно показывать кампанию */
    std::set<std::string> ignored_accounts() const { return ignored_accounts_; }

    /** \brief  Покрытие рекламных площадок:

      По умолчанию равно Show_Allowed.

      \see ShowCoverage
    */
    ShowCoverage show_coverage() const { return show_coverage_; }

    /** \brief  Дни недели, в которые нужно отображать кампанию */
    std::set<boost::date_time::weekdays> days_of_week() const {
	return days_of_week_;
    }

    /** \brief  Время (UTC), в которое начинается показ кампании. */
    boost::posix_time::time_duration start_show_time() const {
	return start_show_time_;
    }

    /** \brief  Время (UTC), в которое заканчивается показ кампании */
    boost::posix_time::time_duration end_show_time() const {
	return end_show_time_;
    }

    /** \brief  Ограничение на количество показов в сутки, 0 -- если нет ограничения */
    unsigned int impressions_per_day_limit() const {
	return impressions_per_day_limit_;
    }

    /** \brief  Множество категорий, к которым относится кампания */
    const std::set<std::string> &categories() const { return categories_; }

    /** \brief  Сбрасывает правила в значения по умолчанию */
    void reset();

    /** \brief  Загружает правила из базы данных.
     *
     * Возвращает true в случае успеха */
    bool load();

    /** \brief  Возвращает true, если объект был загружен из базы данных */
    bool loaded() const { return loaded_; }


private:
    Campaign campaign_;
    std::set<std::string> country_targeting_;
    std::set<std::string> region_targeting_;
    std::set<Informer> allowed_informers_;
    std::set<std::string> allowed_domains_;
    std::set<std::string> allowed_accounts_;
    std::set<Informer> ignored_informers_;
    std::set<std::string> ignored_domains_;
    std::set<std::string> ignored_accounts_;
    ShowCoverage show_coverage_;
    std::set<boost::date_time::weekdays> days_of_week_;
    boost::posix_time::time_duration start_show_time_;
    boost::posix_time::time_duration end_show_time_;
    unsigned int impressions_per_day_limit_;
    std::set<std::string> categories_;

    bool loaded_;
};


/** \brief  Кеш рекламных кампаний */
class CampaignOptionsCache
{
public:
    /** \brief  Возвращает объект CampaignShowOptions для кампании \a c.
     *
     * Объект будет загружен только первый раз, в следующие разы будет
     * использоваться кеш.
     *
     * \see invalidate()
     */
    static CampaignShowOptions *get(const Campaign &c);

    /** \brief  Сбрасывает (очищает) кеш. */
    static void invalidate();

private:
    static std::map<Campaign, CampaignShowOptions *> cache_;
};

#endif // CAMPAIGNSHOWOPTIONS_H
