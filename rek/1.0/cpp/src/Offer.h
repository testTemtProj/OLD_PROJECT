#ifndef OFFER_H
#define OFFER_H

#include <string>
#include <list>
#include <map>

#include "Campaign.h"

class Offers;

/** \brief  Класс описывает рекламное предложение (например, товар или новость). */
class Offer
{
    /// Структура для хранения информации о рекламном предложении.
    struct OfferData {
        OfferData(std::string id) : id(id), valid(false) { }

        std::string id;             ///< ID предложения
        std::string title;          ///< Заголовок
        std::string price;          ///< Цена
        std::string description;    ///< Описание
        std::string url;            ///< URL перехода на предложение
        std::string image_url;      ///< URL картинки
        std::string campaign_id;    ///< ID кампании, к которой относится предложение

        bool valid;                 ///< Является ли запись действительной.
    };

    Offer(OfferData *data) : d(data) { }

public:
    Offer(std::string id);

    /** ID предложения */
    std::string id() const { return d->id; }

    /** Заголовок */
    std::string title() const { return d->title; }

    /** Цена */
    std::string price() const { return d->price; }

    /** Текст описания */
    std::string description() const { return d->description; }

    /** Ссылка, на которую ведёт предложение */
    std::string url() const { return d->url; }

    /** Ссылка изображения */
    std::string image_url() const { return d->image_url; }

    /** ID рекламной кампании, к которой относится товарное предложение */
    std::string campaign_id() const { return d->campaign_id; }

    /** Является ли предложение действительным (т.е. найденным и загруженным) */
    bool valid() const { return d->valid; }

    bool operator==(const Offer &other) const { return d == other.d; }
    bool operator<(const Offer &other) const { return d < other.d; }

    friend class Offers;

private:
    OfferData *d;

//    // Список предложений по id
//    static std::map<std::string, OfferData*> &data_by_id() {
//	static std::map<std::string, OfferData*> data_by_id_;
//	return data_by_id_;
//    }
};


/** Модель рекламных предложений */
class Offers
{
    Offers() { }

public:
    /** Возвращает singleton объект Offers */
    static Offers *x() {
	static Offers *instance_ = new Offers;
	return instance_;
    }

    /** Загружает все товарные предложения */
    void loadFromDatabase();

    /** Загружает товарные предложения по кампании campaign */
    void loadByCampaign(const Campaign &campaign);

    /** Загружает товарные предложения с сервера через XmlRpc */
    bool loadFromServer();

    /** Возвращает список предложений по кампании campaign.
	Если кампания не найдена, вернёт пустой список. */
    std::list<Offer> offers_by_campaign(const Campaign &campaign);

    /** Количество загруженных предложений */
    int count() const { return data_by_id_.size(); }

    /** Очищает все предложения. Существующие загруженные предложения
	становятся недействительными (valid == false), однако из памяти
	во избежание сбоев не удаляются. */
    void invalidate();
    void invalidate(const Campaign &campaign);

    friend class Offer;

private:
    std::map<std::string, Offer::OfferData*> data_by_id_;
    std::map<Campaign, std::list<Offer> > offers_by_campaign_;

    void _loadFromQuery(const mongo::Query &query);
};

#endif // OFFER_H
