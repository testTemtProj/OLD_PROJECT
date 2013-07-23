#include "DB.h"
#include <map>
#include <glog/logging.h>
#include <boost/algorithm/string.hpp>
#include "Informer.h"

using namespace std;
using namespace mongo;

/** Ищет данные информера по id, если не находит, то вставляет пустой элемент,
    у которого valid = false
*/
Informer::Informer(std::string id)
{
    boost::to_lower(id);
    d = informer_data_by_id_[id];
    if (!d) {
	d = new InformerData(id);
	informer_data_by_id_[id] = d;
    }
}

/** Возвращает множество заблокированных аккаунтов */
std::set<std::string> Informer::GetBlockedAccounts()
{
    std::set<std::string> result;
    mongo::DB db;
    unique_ptr<mongo::DBClientCursor> cursor =
	    db.query("users", QUERY("blocked" <<
				    BSON("$in" << BSON_ARRAY("banned" <<
							     "light"))));
    while (cursor->more()) {
	result.insert(cursor->next().getStringField("login"));
    }
    return result;
}


/** Помечает все информеры как невалидные */
void Informer::invalidateAll()
{
    for (auto it = informer_data_by_id_.begin();
         it != informer_data_by_id_.end(); ++it) {
        it->second->valid = false;
    }
}

/** Перезагружает информер \a informer */
bool Informer::loadInformer(const Informer &informer)
{
    return _loadFromQuery(QUERY("guid" << informer.id()));
}


/** Загружает данные обо всех информерах */
bool Informer::loadAll()
{
    return _loadFromQuery(mongo::Query());
}


/** Загружает информеры, попадающие под запрос \a query */
bool Informer::_loadFromQuery(const mongo::Query &query)
{
    mongo::DB db;
    unique_ptr<mongo::DBClientCursor> cursor = db.query("informer", query);
    std::set<std::string> blocked_accounts = GetBlockedAccounts();
    int count = 0, skipped = 0;
    while (cursor->more()) {
	mongo::BSONObj x = cursor->next();
	string id = x.getStringField("guid");
	boost::to_lower(id);
	if (id.empty()) {
	    skipped++;
	    continue;
	}

	InformerData *data = informer_data_by_id_[id];
	if (!data) {
	    data = new InformerData(id);
	    informer_data_by_id_[id] = data;
	}
    
    int mainHeight;
    int mainWidth;
    int borderWidth;
    std::string tmp;
    mongo::BSONElement mainHeightEl;
    mongo::BSONElement mainWidthEl;
    mongo::BSONElement borderWidthEl;
    try
    {
        mainHeightEl = x.getFieldDotted("admaker.Main.height");
        switch (mainHeightEl.type()) {
        case mongo::NumberInt:
            mainHeight = mainHeightEl.numberInt();
            break;
        case mongo::String:
            tmp = mainHeightEl.str();
            tmp = tmp.replace(tmp.find("px"),2,std::string());
            mainHeight = boost::lexical_cast<int>(tmp);
            break;
        default:
            mainHeight = x.getIntField("height");
        }
    }
    catch (std::exception const &ex)
    {
        mainHeight = x.getIntField("height");
        LOG(ERROR) << "exception " << typeid(ex).name() << ": " << ex.what();
    }
    try
    {
        mainWidthEl = x.getFieldDotted("admaker.Main.width");
        switch (mainWidthEl.type()) {
        case mongo::NumberInt:
            mainWidth = mainWidthEl.numberInt();
            break;
        case mongo::String:
            tmp = mainWidthEl.str();
            tmp = tmp.replace(tmp.find("px"),2,std::string());
            mainWidth = boost::lexical_cast<int>(tmp);
            break;
        default:
            mainWidth = x.getIntField("width");
        }
    }
    catch (std::exception const &ex)
    {
        mainWidth = x.getIntField("width");
        LOG(ERROR) << "exception " << typeid(ex).name() << ": " << ex.what();
    }
    try
    {
        borderWidthEl = x.getFieldDotted("admaker.Main.borderWidth");
        switch (borderWidthEl.type()) {
        case mongo::NumberInt:
            borderWidth = borderWidthEl.numberInt();
            break;
        case mongo::String:
            tmp = borderWidthEl.str();
            if (tmp.length() > 0)
            {
                borderWidth = boost::lexical_cast<int>(tmp);
            }
            else
            {
                borderWidth = 0;
            }
            break;
        default:
            borderWidth = 0;
        }
    }
    catch (std::exception const &ex)
    {
        borderWidth = 0;
        LOG(ERROR) << "exception " << typeid(ex).name() << ": " << ex.what();
    }

    mainHeight += borderWidth * 2;
    mainWidth += borderWidth * 2;

	data->height = mainHeight;
	data->width = mainWidth;
	data->domain = x.getStringField("domain");
	data->title = x.getStringField("title");
	data->user = x.getStringField("user");
	data->blocked = (blocked_accounts.find(data->user) !=
			 blocked_accounts.end());

	data->valid = true;
	count++;
    }
    LOG(INFO) << "Loaded " << count << " informers";
    if (skipped)
	LOG(WARNING) << skipped << " informers with empty id skipped";
    return true;
}


bool Informer::operator==(const Informer &other) const
{
    return this->id() == other.id();
}

bool Informer::operator<(const Informer &other) const
{
    return this->id() < other.id();
}


std::map<std::string, Informer::InformerData*> Informer::informer_data_by_id_;
