#define BOOST_TEST_DYN_LINK

#include <boost/test/unit_test.hpp>
#include <boost/lexical_cast.hpp>
#include <boost/xpressive/xpressive.hpp>
#include <glog/logging.h>
#include <algorithm>
#include "../src/DB.h"
#define private public
#include "../src/Core.h"
#define public private
#include "../src/Rules.h"
#include "../src/Informer.h"

BOOST_AUTO_TEST_SUITE( TestCore )


/** Проверка на получение правильных предложений из ядра */
BOOST_AUTO_TEST_CASE( TestOffers )
{
    mongo::DB db;
    db.dropDatabase();
    mongo::DB::addDatabase("log", "localhost", "test_log", false);
    Core::Params params;
    Core core;

    // Создаём две кампании
    mongo::BSONObj campaign1_bson = BSON(
	    "guid" << "CAMP#01" <<
	    "title" << "Campaign 1" <<
	    "showCoverage" << "all");		    // FIX: showConditions...
    mongo::BSONObj campaign2_bson = BSON(
	    "guid" << "CAMP#02" <<
	    "title" << "Campaign 2" <<
	    "showCoverage" << "all");		    // FIX: showConditions...
    db.insert("campaign", campaign1_bson, true);
    db.insert("campaign", campaign2_bson, true);

    // Подготавливаем 5 предложений для первой кампании и 10 для второй
    for (int i = 1; i <= 5; i++) {
	std::string num = boost::lexical_cast<std::string>(i);
	mongo::BSONObj offer = BSON(
		"guid" << "Offer#0" + num <<
		"title" << "Offer " + num <<
		"image" << "img.jpg" <<
		"campaignId" << "CAMP#01");
	db.insert("offer", offer, true);
    }
    for (int i = 0; i < 10; i++) {
	std::string num = boost::lexical_cast<std::string>(i);
	mongo::BSONObj offer = BSON(
		"guid" << "Offer#1" + num <<
		"title" << "Offer 1" + num <<
		"image" << "img.jpg" <<
		"campaignId" << "CAMP#02");
	db.insert("offer", offer, true);
    }


    // Загружаем данные
    core.LoadAllEntities();

    // Проверяем, что всё успешно загрузилось
    Campaign camp1("CAMP#01");
    Campaign camp2("CAMP#02");
    BOOST_REQUIRE( camp1.valid() && camp2.valid() );
    BOOST_REQUIRE( Offers::x()->offers_by_campaign(camp1).size() == 5);
    BOOST_REQUIRE( Offers::x()->offers_by_campaign(camp2).size() == 10);

    // Выполняем тест
    const int iterations = 5000;
    const int total_campaings = 2;
//    const int total_offers = 15;
    const int offers_per_informer = 3;
    std::map<Offer, int> offers_counter;
    std::map<Campaign, int> campaign_counter;
    int duplicates = 0;	    // Кол-во информеров с повторяющимися предложениями

    for (int i = 0; i < iterations; i++) {
	std::vector<Offer> offers = core.getOffers(offers_per_informer, params);
	BOOST_REQUIRE_EQUAL( offers.size(), offers_per_informer );
	bool has_duplicates = false;
	for (auto it = offers.begin(); it != offers.end(); it++) {
	    offers_counter[*it]++;
	    campaign_counter[Campaign(it->campaign_id())]++;
	    if (std::count(offers.begin(), offers.end(), *it) > 1)
		has_duplicates = true;
	}
	if (has_duplicates)
	    duplicates++;
    }

    // Проверки на равномерность распределения кампаний
    BOOST_CHECK_CLOSE( double(campaign_counter[Campaign("CAMP#01")]),
		       iterations * offers_per_informer / total_campaings, 2);
    BOOST_CHECK_CLOSE( double(campaign_counter[Campaign("CAMP#02")]),
		       iterations * offers_per_informer / total_campaings, 2);

    // TODO: Проверки на равномерность распределения предложений

    // Допустимое число дубликатов (не более 2% от общего числа показов)
    BOOST_CHECK_LT( double(duplicates), iterations * 0.02);
}

bool is_offer_valid(const Offer &offer)
{
    return offer.valid();
}


/** Возвращает количество повторяющихся предложений */
int duplicates_count(std::vector<Offer> offers)
{
    std::sort(offers.begin(), offers.end());
    int unique_count = 0;
    auto end_unique = std::unique(offers.begin(), offers.end());
    for (auto it = offers.begin(); it != end_unique; ++it, ++unique_count) ;
    return offers.size() - unique_count;
}


/** Проверка функции, подсчитывающей количество уникальных предолжений */
BOOST_AUTO_TEST_CASE( TestDuplicatesCount )
{
    std::vector<Offer> offers1;
    offers1.push_back(Offer("1"));
    offers1.push_back(Offer("2"));
    offers1.push_back(Offer("3"));
    
    std::vector<Offer> offers2;
    offers2.push_back(Offer("1"));
    offers2.push_back(Offer("1"));
    offers2.push_back(Offer("2"));

    BOOST_REQUIRE_EQUAL( duplicates_count(offers1), 0 );
    BOOST_REQUIRE_EQUAL( duplicates_count(offers2), 1 );
}


/** Проверка борьбы с дубликатами в случае, когда одна из кампаний содержит
 *  мало предложений */
BOOST_AUTO_TEST_CASE( TestDuplicatesWithSmallCampaigns )
{
    mongo::DB db;
    db.dropDatabase();
    Core::Params params;
    Core core;

    // Создаём кампанию с одним предложением
    db.insert("campaign", BSON(
        "guid" << "CAMP#01" <<
        "title" << "Campaign 1" <<
        "showCoverage" << "all"));

    db.insert("offer", BSON(
        "guid" << "Offer#01-1" <<
        "title" << "Offer 01-1" <<
        "image" << "img.jpg" <<
        "campaignId" << "CAMP#01"));

    // Создаём кампанию с десятью предложениями
    db.insert("campaign", BSON(
        "guid" << "CAMP#02" <<
        "title" << "Campaign 2" <<
        "showCoverage" << "all"));

    for (int i = 1; i <= 10; i++) {
        std::string num = boost::lexical_cast<std::string>(i);
        db.insert("offer", BSON(
            "guid" << "Offer#02-" + num <<
            "title" << "Offer 02-" + num <<
            "image" << "img.jpg" <<
            "campaignId" << "CAMP#02"),
            true);
    }

    // Загружаем
    core.LoadAllEntities();

    // Выполняем тест
    const int iterations = 5000;
    const int offers_per_informer = 3;
    int duplicate_cases = 0;
    
    for (int i = 0; i < iterations; i++) {
        std::vector<Offer> offers = core.getOffers(offers_per_informer, params);
        int valid_count =
            std::count_if(offers.begin(), offers.end(), is_offer_valid);
        BOOST_REQUIRE_EQUAL( valid_count, offers_per_informer );
        if (duplicates_count(offers))
            duplicate_cases++;
    }

    // Допустимое число дубликатов (не более 2% от числа показов)
    BOOST_CHECK_LT(double(duplicate_cases), iterations * 0.02);

}


/** Проверка процедуры обработки запроса */
BOOST_AUTO_TEST_CASE (TestProcess )
{
    // Подготовка баз данных
    mongo::DB::addDatabase("log", "localhost", "test_log", false);
    mongo::DB db_log("log");
    db_log.db()->dropDatabase(db_log.database());
    mongo::DB db;
    db.db()->dropDatabase(db.database());
    Core::Params params;
    Core core;

    // Создаём 5 тестовых предложений, информер и кампанию
    mongo::BSONObj informer_bson = mongo::fromjson(
	    "{guid: 'INF#01', "
	    "title: 'Informer 01', "
	    "admaker: {Main: {itemsNumber: 10}}"
	    "}");
    mongo::BSONObj campaign_bson = BSON(
	    "guid" << "CAMP" <<
	    "title" << "Campaign" <<
	    "showConditions" << mongo::fromjson("{showCoverage: 'all'}"));
    db.insert("informer", informer_bson, true);
    db.insert("campaign", campaign_bson, true);
    for (int i = 1; i <= 5; i++) {
	std::string num = boost::lexical_cast<std::string>(i);
	mongo::BSONObj offer = BSON(
		"guid" << "Offer#0" + num <<
		"title" << "Offer " + num <<
		"image" << "img.jpg" <<
		"campaignId" << "CAMP");
	db.insert("offer", offer, true);
    }

    // Загружаем данные
    core.LoadAllEntities();
    Informer informer("INF#01");
    BOOST_REQUIRE( informer.valid() );
    BOOST_REQUIRE( informer.capacity() == 10);


    {	// В тестовом режиме отметки не записываются
	core.Process(Core::Params()
		     .informer("INF#01")
		     .ip("127.0.0.1")
		     .test_mode(true));
	std::unique_ptr<mongo::DBClientCursor> cursor =
		db_log.query("log.impressions", mongo::Query() );
	int log_impressions_count = cursor->itcount();
	BOOST_CHECK_EQUAL(log_impressions_count, 0);
    }


    {	// В базу данных журнала должны записаться отметки о показе рекламы
	db_log.dropCollection("log.impressions");
	core.Process(Core::Params()
		     .informer("inf#01")
		     .ip("127.0.0.1"));
	std::unique_ptr<mongo::DBClientCursor> cursor =
		db_log.query("log.impressions", mongo::Query() );
	int log_impressions_count = 0;
	if (cursor->more() ) {
	    mongo::BSONObj x = cursor->next();
	    BOOST_CHECK_EQUAL( x.getStringField("ip"), "127.0.0.1" );
	    BOOST_CHECK_EQUAL( x.getStringField("inf"), "inf#01" );
	    BOOST_CHECK_EQUAL( x.getStringField("ip"), "127.0.0.1" );
	    BOOST_CHECK_EQUAL( std::string(x.getStringField("id")).substr(0, 6),
			       "Offer#");
	    BOOST_CHECK_EQUAL( std::string(x.getStringField("title")).substr(0, 6),
			       "Offer ");
	    BOOST_CHECK_EQUAL( x.getBoolField("social"), false );
	    std::string token = x.getStringField("token");
	    BOOST_CHECK( !token.empty() );
	    log_impressions_count++;
	}
	log_impressions_count += cursor->itcount();
	BOOST_CHECK_EQUAL(log_impressions_count, informer.capacity());
    }

    {	// Токены должны быть уникальными для каждого элемента показа
	db_log.dropCollection("log.impressions");
	core.Process(Core::Params()
		     .informer("INF#01")
		     .ip("127.0.0.1"));
	std::unique_ptr<mongo::DBClientCursor> cursor =
		db_log.query("log.impressions", mongo::Query() );
	std::set<std::string> unique_tokens;
	while (cursor->more()) {
	    mongo::BSONObj x = cursor->next();
	    unique_tokens.insert(x.getStringField("token"));
	}
	BOOST_CHECK_EQUAL(unique_tokens.size(), informer.capacity());
    }
}


/** TODO: Проверка работоспособности менеджера очередей сообщений (MQ) */
BOOST_AUTO_TEST_CASE( TestMQ )
{
}


/** Проверка экранирования JSON-строк */
BOOST_AUTO_TEST_CASE( TestEscapeJson )
{
    std::string s("Unsafe string: ',\",\t,/,\b,\r\n");
    BOOST_CHECK_EQUAL(Core::EscapeJson(s),
		      "Unsafe string: \\',\\\",\\t,\\/,\\b,\\r\\n");
}


/** Проверка отдачи предложений в JSON */
BOOST_AUTO_TEST_CASE( TestJson )
{
    // Подготовка баз данных
    mongo::DB::addDatabase("log", "localhost", "test_log", false);
    mongo::DB db_log("log");
    db_log.dropDatabase();
    mongo::DB db;
    db.dropDatabase();
    Core::Params params;
    Core core;

    // Создаём 1 тестовое предложение, информер и кампанию
    mongo::BSONObj informer_bson = mongo::fromjson(
	    "{guid: 'INF#01', "
	    "title: 'Informer 01', "
	    "admaker: {Main: {itemsNumber: 2}}"
	    "}");
    mongo::BSONObj campaign_bson = BSON(
	    "guid" << "CAMP" <<
	    "title" << "Campaign" <<
	    "showConditions" << mongo::fromjson("{showCoverage: 'all'}"));
    db.insert("informer", informer_bson, true);
    db.insert("campaign", campaign_bson, true);
    mongo::BSONObj offer = BSON(
	    "guid" << "Offer#1" <<
	    "title" << "Offer 1" <<
	    "description" << "Description" <<
	    "price" << "123 грн." <<
	    "image" << "http://example.com/image.jpeg" <<
	    "url" << "http://example.com/redirect" <<
	    "campaignId" << "CAMP");
    db.insert("offer", offer, true);

    // Загружаем данные
    core.LoadAllEntities();
    Informer informer("INF#01");
    BOOST_REQUIRE( informer.valid() );
    BOOST_REQUIRE( informer.capacity() == 2);

    // Поскольку у нас только одно предложение, сервис может отдать только
    // его в двух экземлярах (2 --- это ёмкость информера)
    std::string json =
	    "["
	    "{\"id\": \"Offer#1\","
	    "\"title\": \"Offer 1\","
	    "\"description\": \"Description\","
	    "\"price\": \"123 грн.\","
	    "\"image\": \"http:\\/\\/example.com\\/image.jpeg\","
	    "\"url\": \"REPLACED_URL\","
	    "\"token\": \"test\""
	    "},"
	    "{\"id\": \"Offer#1\","
	    "\"title\": \"Offer 1\","
	    "\"description\": \"Description\","
	    "\"price\": \"123 грн.\","
	    "\"image\": \"http:\\/\\/example.com\\/image.jpeg\","
	    "\"url\": \"REPLACED_URL\","
	    "\"token\": \"test\""
	    "}"
	    "]";
    std::string result = core.Process(params
				      .json(true).informer("INF#01")
				      .test_mode(true));

    // Поскольку URL редиректа проверить очень сложно, просто заменяем его
    // на строку 'REPLACED_URL'
    // TODO: Когда формат ссылки перенаправления устаканится, дописать тест
    auto url_regexp =
	    boost::xpressive::sregex::compile("\"url\": \"([^\"']*)\"");
    result = regex_replace(result, url_regexp, "\"url\": \"REPLACED_URL\"");

    BOOST_CHECK_EQUAL( result, json );
}


template<class T>
bool contains(const std::vector<T> &container, const T &item)
{
    return std::find(container.begin(), container.end(), item) !=
	    container.end();
}

/** Проверка исключения предложений из показа */
BOOST_AUTO_TEST_CASE( TestExcludedOffers )
{
    mongo::DB db;
    db.db()->dropDatabase(db.database());
    mongo::DB::addDatabase("log", "localhost", "test_log", false);
    Core core;

    mongo::BSONObj campaign_bson = BSON(
	    "guid" << "CAMP" <<
	    "title" << "Campaign" <<
	    "showConditions" << mongo::fromjson("{showCoverage: 'all'}"));
    db.insert("campaign", campaign_bson, true);

    // Создаём 5 предложений
    for (int i = 1; i <= 5; i++) {
	std::string num = boost::lexical_cast<std::string>(i);
	mongo::BSONObj offer = BSON(
		"guid" << "offer#0" + num <<
		"title" << "offer " + num <<
		"image" << "img.jpg" <<
		"campaignId" << "CAMP");
	db.insert("offer", offer, true);
    }

    // Загружаем данные
    core.LoadAllEntities();

    std::vector<std::string> excluded;
    excluded.push_back("offer#01");
    excluded.push_back("offer#03");

    Core::Params params;
    std::vector<Offer> offers = core.getOffers(10,
					       params.excluded_offers(excluded)
					       );
    BOOST_CHECK( contains(offers, Offer("offer#02")) );
    BOOST_CHECK( contains(offers, Offer("offer#04")) );
    BOOST_CHECK( contains(offers, Offer("offer#05")) );
    BOOST_REQUIRE(!contains(offers, Offer("offer#01")) );
    BOOST_REQUIRE(!contains(offers, Offer("offer#03")) );
}


/** Проверка выдачи пользовательского кода при отсутствии релевантной рекламы */
BOOST_AUTO_TEST_CASE( TestNonRelevantUserCode )
{
    // Социальная кампания
    mongo::BSONObj campaign_obj = mongo::fromjson(
	    "{guid: 'ADV-0001',		   "
	    "social: true		   "
	    "}");
    mongo::BSONObj informer_obj = mongo::fromjson(
	    "{guid: 'INF-0001',		   "
	    "nonRelevant: {		   "
	    "	action: 'usercode',	   "
	    "	userCode: 'user code sample' "
	    " }}");

    mongo::DB db;
    db.insert("campaign", campaign_obj, true);
    db.insert("informer", informer_obj, true);

    Campaign::loadAll();
    Informer::loadAll();

    {	// При данных настройках должен возвращаться пользовательский код
	Core core;
	Core::Params params;
	std::string result = core.Process(params.informer("INF-0001"));
	BOOST_CHECK_EQUAL( result, "user code sample" );
    }
}


bool is_valid_offer(const Offer &offer)
{
    return offer.valid();
}

/** Количество действительных предложений по кампании campaign */
int count_valid_offers_by_campaign(const std::string &campaign_id)
{
    list<Offer> offers = Offers::x()->offers_by_campaign(Campaign(campaign_id));
    return count_if(offers.begin(), offers.end(), is_valid_offer);
}


/** Проверка корректного сброса кешей и перезагрузки сущностей при
    обновлении кампаний */
BOOST_AUTO_TEST_CASE( TestReloadEntities )
{
    mongo::DB db;
    db.dropDatabase();
    Informer::invalidateAll();
    BOOST_CHECK_EQUAL( count_valid_offers_by_campaign("CAMP"), 5 );

    // Создаём 5 тестовых предложений, информер и кампанию и загружаем их
    mongo::BSONObj informer_bson = mongo::fromjson(
	    "{guid: 'INF#01', "
	    "title: 'Informer 01', "
	    "admaker: {Main: {itemsNumber: 10}}"
	    "}");
    mongo::BSONObj campaign_bson = BSON(
	    "guid" << "CAMP" <<
	    "title" << "Campaign" <<
	    "showConditions" << mongo::fromjson("{showCoverage: 'all'}"));
    db.insert("informer", informer_bson, true);
    db.insert("campaign", campaign_bson, true);
    for (int i = 1; i <= 5; i++) {
	std::string num = boost::lexical_cast<std::string>(i);
	mongo::BSONObj offer = BSON(
		"guid" << "Offer#0" + num <<
		"title" << "Offer " + num <<
		"image" << "img.jpg" <<
		"campaignId" << "CAMP");
	db.insert("offer", offer, true);
    }

    Core core;
    BOOST_CHECK_EQUAL( count_valid_offers_by_campaign("CAMP"), 5);
    RandomEntity<Offer> offers = core.offers_by_campaign(Campaign("CAMP"));
    BOOST_CHECK_EQUAL( offers.count(), 5 );
    core.LoadAllEntities();
    BOOST_CHECK( Informer("INF#01").valid() );
    BOOST_CHECK(!Informer("INF#02").valid() );
    BOOST_CHECK( Offer("Offer#01").valid()  );
    BOOST_CHECK(!Offer("Offer#11").valid()  );

    offers = core.offers_by_campaign(Campaign("CAMP"));
    BOOST_CHECK_EQUAL( offers.count(), 5 );

    // Добавляем товары и перезагружаем всё ещё раз
    for (int i = 11; i <= 15; i++) {
	std::string num = boost::lexical_cast<std::string>(i);
	mongo::BSONObj offer = BSON(
		"guid" << "Offer#0" + num <<
		"title" << "Offer " + num <<
		"image" << "img.jpg" <<
		"campaignId" << "CAMP");
	db.insert("offer", offer, true);
    }
    core.LoadAllEntities();
    // Теперь по кампании CAMP должно быть 10 товаров
    offers = core.offers_by_campaign(Campaign("CAMP"));
    BOOST_CHECK_EQUAL( count_valid_offers_by_campaign("CAMP"), 10);
    BOOST_CHECK_EQUAL( offers.count(), 10 );

    // Удаляем товары и перезагружаем всё
    db.dropCollection("offer");
    core.LoadAllEntities();
    offers = core.offers_by_campaign(Campaign("CAMP"));
    BOOST_CHECK_EQUAL( count_valid_offers_by_campaign("CAMP"), 0);
    BOOST_CHECK_EQUAL( offers.count(), 0 );
}


BOOST_AUTO_TEST_SUITE_END()
