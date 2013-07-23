#include "Campaign.h"
#include "CampaignShowOptions.h"
#include "DB.h"
#include <glog/logging.h>

	/** \brief  Конструктор

        \param id        Идентификатор рекламной кампании
	*/
Campaign::Campaign(const std::string &id)
{
    d = cache()[id];
    if (!d) {
	d = new CampaignData(id);
	cache()[id] = d;
    }
}

	/** \brief  Закгрузка всех рекламных кампаний из базы данных  Mongo 

     */
void Campaign::loadAll()
{
    all().clear();
    CampaignOptionsCache::invalidate();
    mongo::DB db;
    auto cursor = db.query("campaign", mongo::Query());
    while (cursor->more())
    {
        mongo::BSONObj x = cursor->next();
        std::string id = x.getStringField("guid");
        if (id.empty())
        {
            LOG(WARNING) << "Campaign with empty id skipped";
            continue;
        }

        CampaignData *data = cache()[id];
        if (!data)
        {
            data = new CampaignData(id);
            cache()[id] = data;
        }
        data->title = x.getStringField("title");
        data->project = x.getStringField("project");
        data->social = x.getBoolField("social");
        data->valid = true;
        all().push_back(Campaign(id));
    }
    LOG(INFO) << "Loaded " << all().size() << " campaigns";
}
