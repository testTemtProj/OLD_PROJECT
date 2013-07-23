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

	data->teasersCss = x.getStringField("css");
	data->bannersCss = x.getStringField("css_banner");
	data->height = x.getIntField("height");
	data->width = x.getIntField("width");
	data->height_banner = x.getIntField("height_banner");
	data->width_banner = x.getIntField("width_banner");
	data->domain = x.getStringField("domain");
	data->title = x.getStringField("title");
	data->user = x.getStringField("user");
	data->blocked = (blocked_accounts.find(data->user) !=
			 blocked_accounts.end());

	// Свойство capacity может храниться в mongo и строкой, и int'ом
	mongo::BSONElement capacity_element =
		x.getFieldDotted("admaker.Main.itemsNumber");
	switch (capacity_element.type()) {
	case mongo::NumberInt:
	    data->capacity = capacity_element.numberInt();
	    break;
	case mongo::String:
	    data->capacity =
		    boost::lexical_cast<int>(capacity_element.str());
	    break;
	default:
	    data->capacity = 0;
	}

	// Действие при отсутствии релевантной рекламы
	std::string non_relevant = x.getFieldDotted("nonRelevant.action").str();
	if (non_relevant == "usercode") {
	    data->nonrelevant = Informer::Show_UserCode;
	    data->user_code = x.getFieldDotted("nonRelevant.userCode").str();
	} else {
	    data->nonrelevant = Informer::Show_Social;
	    data->user_code = "";
	}

	// Тематические категории
	LoadCategoriesByDomain(data->categories, data->domain);

	data->valid = true;
	count++;
    }
    LOG(INFO) << "Loaded " << count << " informers";
    if (skipped)
	LOG(WARNING) << skipped << " informers with empty id skipped";
    return true;
}

/** Загружает множество категорий, к которым относится домен ``domain``
    в множество ``categories`` */
void Informer::LoadCategoriesByDomain(set<string> &categories,
				      const std::string &domain)
{
    mongo::DB db;
    mongo::BSONObj item = db.findOne("domain.categories",
				     QUERY("domain" << domain));
    if (!item.isValid())
	return;
    mongo::BSONObjIterator iter = item.getObjectField("categories");
    while (iter.more()) {
	categories.insert(iter.next().str());
    }
    return;
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
