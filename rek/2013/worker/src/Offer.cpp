#include "DB.h"
#include <glog/logging.h>
#include "Offer.h"

using namespace std;

Offer::Offer(std::string id)
{
    Offer::OfferData *data = Offers::x()->data_by_id_[id];
    if (!data) {
	data = new OfferData(id);
	Offers::x()->data_by_id_[id] = data;
    }
    d = data;
}


/** Загружает товарные предложения, относящиеся к кампании \a campaign */
void Offers::loadByCampaign(const Campaign &campaign)
{
    invalidate(campaign); 
    _loadFromQuery(QUERY( "campaignId" << campaign.id() ));
}


/** Загружает все товарные предложения из MongoDb */
void Offers::loadFromDatabase()
{
    invalidate();
    _loadFromQuery(mongo::Query());
}

/** Загружает предложения, попадающие под запрос \a query.
 *
 *  Не занимается предварительной чистой устаревших предложений!
 */
void Offers::_loadFromQuery(const mongo::Query &query)
{
    mongo::DB db;
    auto cursor = db.query("offer", query);
    int count = 0, skipped = 0;
    while (cursor->more()) {
        mongo::BSONObj x = cursor->next();
        string id = x.getStringField("guid");
        if (id.empty()) {
            skipped++;
            continue;
        }

        string image = x.getStringField("image");
        string swf = x.getStringField("swf");
        if (image.empty()) {
            if (swf.empty()){
                skipped++;
                continue;
            }
        }

        Offer::OfferData *data = data_by_id_[id];
        if (!data) {
            data = new Offer::OfferData(id);
            data_by_id_[id] = data;
        }

        data->campaign_id = x.getStringField("campaignId");
        data->title = x.getStringField("title");
        data->description = x.getStringField("description");
        data->image_url = image;
        data->price = x.getStringField("price");
        data->url = x.getStringField("url");
        data->valid = true;
        data->type = x.getStringField("type");
        data->isOnClick = x.getBoolField("isOnClick");
        data->rating = mongo::DB::toFloat(x.getField("rating"));
        data->uniqueHits = x.getIntField("uniqueHits");
        data->branch = "L0";
        data->conformity = "place";
        data->matching = "";
        if (data->uniqueHits == INT_MIN)
        {
            data->uniqueHits = -1;
        }	
        data->height = x.getIntField("height");
        data->width = x.getIntField("width");

        if (data->type=="banner")
        {
            //проверяем swf
            //если такого поля нет, то строка swf будет пустой. иначе - она будет равняться содержимому поля.
            if (!swf.empty())
            {
                data->swf = swf;
            }
        }
        
        
        
        offers_by_campaign_[data->campaign_id].push_back(Offer(data));
        count++;
	
    }
    LOG(INFO) << "Loaded " << count << " offers";
    if (skipped)
        LOG(WARNING) << skipped << " offers with empty id or image skipped";
}

/** Возвращает список предложений по кампании campaign_id */
std::list<Offer> Offers::offers_by_campaign(const Campaign &campaign)
{
    auto it = offers_by_campaign_.find(campaign);
    if (it != offers_by_campaign_.end())
	return it->second;
    else
	return std::list<Offer>();
}


void Offers::invalidate()
{
    // TODO: В данный момент старые предложения не удаляются из памяти, а
    // лишь помечаются как invalid. Нужно проверить код, не могут ли где
    // где зависать ссылки на invalid предложения и если нет, то удалять их
    // из памяти (а то вроде сервис со временем будет всё пухнуть и пухнуть
    // в оперативке).
    offers_by_campaign_.clear();
    for (auto it = data_by_id_.begin(); it != data_by_id_.end(); it++)
	it->second->valid = false;
}


void Offers::invalidate(const Campaign &campaign)
{
    std::list<Offer> &offers = offers_by_campaign_[campaign];
    for (auto it = offers.begin(); it != offers.end(); ++it) {
        it->d->valid = false;
    }
    offers_by_campaign_.erase(campaign);
}

