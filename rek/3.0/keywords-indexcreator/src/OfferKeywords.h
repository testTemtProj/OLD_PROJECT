#ifndef INFORMER_H
#define INFORMER_H

#include <string>
#include <map>
#include <set>

/**
Стуктура, описывающая параметры конкретного рекламного предложения
*/ 
struct OfferKeywordsData {
        std::string guid;         ///< GUID РП
        std::string title;      ///< Заголовок РП
	std::string type;
        std::set<std::string> keywords;   ///< Множество ключевых слов РП
	std::set<std::string> exactly_phrases;   ///< Множество точных фраз РП
	std::set<std::string> phrase_match;   ///< Множество фразовых соответствий РП
	std::set<std::string> minus_words;   ///< Множество минус-слов РП
	std::set<std::string> informer_ids;   ///< Множество идентификаторов информеров, за которыми закреплено данное РП
	std::set<std::string> campaign_ids;   ///< Множество рекламный кампаний, которым принадлежит РП
	std::set<std::string> topic_ids;	///< Множество тематик, которым удовлетворяет РП
	std::string campaign_id;   ///< Множество рекламный кампаний, которым принадлежит РП
		
	bool isOnPlace;

    };



#endif // INFORMER_H
