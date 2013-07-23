#ifndef INFORMER_H
#define INFORMER_H

#include <string>
#include <map>
#include <set>

/**
Стуктура, описывающая параметры конкретного индексируемого документа созданного из рекламного предложения
*/ 
struct OfferKeywordsData {
    std::string guid;                       ///< GUID РП
	std::string type;                       ///< Тип РП
	std::set<std::string> informer_ids;     ///< Множество GUID рекламных блоков, за которыми закреплено данное РП
	std::string campaign_id;                ///< GUID РК, которой принадлежит РП
    std::string rating;                     ///< Рейтинг РП по всей партнёрской сети	
    std::string isOnClick;                  ///< Реклама по кликам или по показам
    std::string contextOnly;                ///< Только контекстная реклама
    std::string retargeting;                ///< Только ретаргетинг реклама
	std::string category_ids;               ///< GUID категори к которой относиться данное РП
};

struct OfferInformerRating {
    std::string offer;          ///< GUID рекламного предложения
    std::string informer;       ///< GUID рекламного блока
	std::string rating;         ///< Рейтинг РП внутри данного рекламного блока
};


#endif // INFORMER_H
