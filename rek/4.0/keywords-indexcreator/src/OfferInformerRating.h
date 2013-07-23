#ifndef INFORMER_H
#define INFORMER_H

#include <string>
#include <map>
#include <set>

/**
Стуктура, описывающая параметры конкретного рекламного предложения
*/ 
struct OfferInformerRating {
        std::string offer;         ///< GUID рекламного предложения
        std::string informer;      ///< GUID рекламного блока
		std::string rating;			///< Рейтинг РП внутри данного рекламного блока
        

    };



#endif // INFORMER_H
