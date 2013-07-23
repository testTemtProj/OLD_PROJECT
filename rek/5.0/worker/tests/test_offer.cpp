#include <boost/test/auto_unit_test.hpp>
#include "../src/Offer.h"
#include "../src/DB.h"


/** Тест загрузки товарных предложний от сервера через XML-RPC */
BOOST_AUTO_TEST_CASE( Test_LoadOffersViaXMLRPC )
{
    // TODO: Запускать тестовый XML-RPC сервер
//    BOOST_REQUIRE( Offers::x()->count() == 0 );
//    bool ok = Offers::x()->loadFromServer();
//    BOOST_REQUIRE( ok );
//    BOOST_CHECK_GT( Offers::x()->count(), 0 );
}

/** Тест загрузки предложений из базы данных */
BOOST_AUTO_TEST_CASE( Test_LoadOffersFromDatabase )
{
    mongo::DB db;
    db.dropCollection("offer");
    Offer offer("offer#01");
    BOOST_CHECK( offer.valid() == false );

    db.insert("offer", BSON(
	    "guid" << "offer#01" <<
	    "title" << "Offer 01" <<
	    "description" << "Offer description" <<
	    "image" << "http://example.com/image.png" <<
	    "price" << "125 $" <<
	    "url" << "http://example.com/offer01.html" <<
	    "campaignId" << "CAMP"
	    ), true);
    Offers::x()->loadFromDatabase();
    BOOST_CHECK( offer.valid() == true );
    BOOST_CHECK( offer.description() == "Offer description" );
    BOOST_CHECK( offer.title() == "Offer 01" );
    BOOST_CHECK( offer.id() == "offer#01" );
    BOOST_CHECK( offer.image_url() == "http://example.com/image.png" );
    BOOST_CHECK( offer.price() == "125 $");
    BOOST_CHECK( offer.url() == "http://example.com/offer01.html" );
    BOOST_CHECK( offer.campaign_id() == "CAMP");

    std::list<Offer> offers = Offers::x()->offers_by_campaign(Campaign("CAMP"));
    BOOST_REQUIRE_EQUAL( offers.size(), 1 );
    BOOST_CHECK( *(offers.begin()) == offer );
}

/** Тест загрузки предложений из определённой кампании */
BOOST_AUTO_TEST_CASE( Test_LoadOffersByCampaign )
{
    mongo::DB db;
    db.dropCollection("offer");
    Offers::x()->invalidate();
    Offer offer1("offer#01");
    Offer offer2("offer#02");
    BOOST_REQUIRE( offer1.valid() == false );
    BOOST_REQUIRE( offer2.valid() == false );

    db.insert("offer", BSON(
	    "guid" << "offer#01" <<
	    "title" << "Offer 01" <<
	    "description" << "Offer description" <<
	    "image" << "http://example.com/image.png" <<
	    "price" << "125 $" <<
	    "url" << "http://example.com/offer01.html" <<
	    "campaignId" << "CAMP1"
	    ), true);

    db.insert("offer", BSON(
	    "guid" << "offer#02" <<
	    "title" << "Offer 02" <<
	    "description" << "Offer description" <<
	    "image" << "http://example.com/image.png" <<
	    "price" << "125 $" <<
	    "url" << "http://example.com/offer02.html" <<
	    "campaignId" << "CAMP2"
	    ), true);

    Offers::x()->loadByCampaign(Campaign("CAMP2"));
    BOOST_REQUIRE( offer1.valid() == false );
    BOOST_REQUIRE( offer2.valid() == true );

    Offers::x()->invalidate(Campaign("CAMP2"));
    BOOST_REQUIRE( offer2.valid() == false );
}

/** Предложения без изображения не должны загружаться */
BOOST_AUTO_TEST_CASE( Test_LoadOffersWithoutImages )
{
    mongo::DB db;
    db.dropCollection("offer");

    db.insert("offer", BSON(
        "guid" << "offer_correct" <<
        "title" << "Correct offer" <<
        "image" << "has image.jpg" <<
        "campaignId" << "CAMP"
    ), true);

    db.insert("offer", BSON(
        "guid" << "offer_incorrect" <<
        "title" << "Incorrect offer" <<
        "campaignId" << "CAMP"
    ), true);

    Offers::x()->loadFromDatabase();
    Offer correct("offer_correct");
    Offer incorrect("offer_incorrect");
    BOOST_CHECK( correct.valid() );
    BOOST_CHECK(!incorrect.valid() );
}

