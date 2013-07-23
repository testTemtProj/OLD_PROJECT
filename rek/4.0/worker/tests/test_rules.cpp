    #define BOOST_TEST_DYN_LINK
#include <boost/test/unit_test.hpp>
#include <boost/date_time.hpp>
#include <algorithm>

#include "../src/Rules.h"
#include "../src/DB.h"


using namespace mongo;
using namespace std;
using namespace boost;
using namespace boost::posix_time;



BOOST_AUTO_TEST_SUITE ( Test_CampaignShowOptions )

/** Проверка значений по умолчанию */
BOOST_AUTO_TEST_CASE ( Defaults )
{
    CampaignShowOptions c(Campaign("advertise #1"));
    BOOST_CHECK( c.country_targeting() == set<string>() );
    BOOST_CHECK( c.region_targeting() == set<string>() );
    BOOST_CHECK( c.allowed_informers() == set<Informer>() );
    BOOST_CHECK( c.ignored_informers() == set<Informer>() );
    BOOST_CHECK( c.show_coverage() == CampaignShowOptions::Show_Allowed );
    BOOST_CHECK( c.days_of_week().size() == 7 );
    BOOST_CHECK( c.impressions_per_day_limit() == 0);
    BOOST_CHECK( c.start_show_time() == time_duration(not_a_date_time) );
    BOOST_CHECK( c.end_show_time() == time_duration(not_a_date_time) );
    BOOST_CHECK( c.categories().empty() );
}


/** Создаёт тестовое правило в базе данных */
void createRuleInDatabase()
{
    DB db;
    db.db()->dropDatabase(db.database());

    BSONObjBuilder allowed, ignored;
    allowed << "accounts" << BSON_ARRAY("account1" )  <<
	       "domains" << BSON_ARRAY("domain1" << "domain2") <<
	       "informers" << BSON_ARRAY("Inf#1");
    ignored << "accounts" << BSON_ARRAY("account3" << "account4")  <<
	       "domains" << BSON_ARRAY("domain3" << "domain4") <<
	       "informers" << BSON_ARRAY("Inf#3" << "Inf#4");
    BSONObj allowed_obj = allowed.obj(),
	    ignored_obj = ignored.obj();
    BSONObj show_conditions =
	    BSON("geoTargeting" << BSON_ARRAY("UA" << "RU" << "PL") <<
		 "regionTargeting" << BSON_ARRAY("Kharkivs'ka Oblast'") <<
		 "showCoverage" << "all" <<
		 "daysOfWeek" << BSON_ARRAY(1 << 2 << 3 << 4 << 5) <<
		 "startShowTime" << BSON("hours" << 7 << "minutes" << 00) <<
		 "endShowTime" << BSON("hours" << 22 << "minutes" << 30) <<
		 "impressionsPerDayLimit" << 1000 <<
		 "categories" << BSON_ARRAY("cat1" << "cat2") <<
		 "allowed" << allowed_obj <<
		 "ignored" << ignored_obj
		 );
    db.insert("campaign",
	      BSON( "title" << "advertise #1" <<
		    "guid" << "ADV-0011" <<
		    "showConditions" << show_conditions ));
}


/** Проверка загрузки объекта из базы данных */
BOOST_AUTO_TEST_CASE ( LoadObject )
{
    using namespace boost::date_time;

    createRuleInDatabase();
    CampaignShowOptions c(Campaign("ADV-0011"));
    c.load();
    BOOST_REQUIRE( c.loaded() == true );
    BOOST_CHECK_EQUAL( c.country_targeting().count("UA"), 1 );
    BOOST_CHECK_EQUAL( c.country_targeting().count("RU"), 1 );
    BOOST_CHECK_EQUAL( c.region_targeting().count("Kharkivs'ka Oblast'"), 1 );
    BOOST_CHECK_EQUAL( c.allowed_informers().size(), 1 );
    BOOST_CHECK_EQUAL( c.allowed_accounts().count("account1"), 1 );
    BOOST_CHECK_EQUAL( c.allowed_domains().count("domain2"), 1 );
    BOOST_CHECK_EQUAL( c.ignored_informers().size(), 2 );
    BOOST_CHECK_EQUAL( c.ignored_accounts().size(), 2 );
    BOOST_CHECK_EQUAL( c.ignored_domains().count("domain4"), 1 );
    BOOST_CHECK_EQUAL( c.days_of_week().size(), 5 );
    BOOST_CHECK_EQUAL( c.days_of_week().count(Monday), 1 );
    BOOST_CHECK_EQUAL( c.days_of_week().count(Saturday), 0 );
    BOOST_CHECK_EQUAL( c.days_of_week().count(Sunday), 0 );
    BOOST_CHECK_EQUAL( c.impressions_per_day_limit(), 1000 );
    BOOST_CHECK_EQUAL( c.show_coverage(), CampaignShowOptions::Show_All );

    std::set<std::string> categories;
    categories.insert("cat1");
    categories.insert("cat2");
    BOOST_CHECK_EQUAL( c.categories().size(), categories.size() );
    BOOST_CHECK( c.categories() == categories );

    BOOST_CHECK( c.start_show_time().hours() == 7 &&
		 c.start_show_time().minutes() == 00 );
    BOOST_CHECK( c.end_show_time().hours() == 22 &&
		 c.end_show_time().minutes() == 30 );
}

BOOST_AUTO_TEST_SUITE_END()


// ---------------------------------------------------------------


BOOST_AUTO_TEST_SUITE( TestRules )


/** Test fixtures: Создаётся в начале каждого теста, члены этого класса
    напрямую доступны тестам
 */
struct F {
    /** Подготовка базы данных к тесту */
    F() {
	db.dropDatabase();
    }

    /** Возвращает true, если element содержится в списке list */
    template<class T>
    bool contains(const list<T> &list, const T &element) {
	return find(list.begin(), list.end( ), element) != list.end();
    }

    list<Campaign> l;
    DB db;
};


/** Проверка ограничений геотаргетинга */
BOOST_FIXTURE_TEST_CASE( TestGeoTargeting, F )
{
    BSONObj rule1 = fromjson(
	    "{guid: 'ADV-0001',                                            "
	    "showConditions: {                                             "
	    "	geoTargeting: ['RU']                                       "
	    "}}"
	    );
    BSONObj rule2 = fromjson(
	    "{guid: 'ADV-0002',                                            "
	    "showConditions: {                                             "
	    "	geoTargeting: ['UA', 'RU']                                 "
	    "}}"
	    );
    BSONObj rule3 = fromjson(
	    "{guid: 'ADV-0003',                                            "
	    "showConditions: {                                             "
	    "	regionTargeting: [\"Kharkivs'ka Oblast'\"]                 "
	    "}}"
	    );
    BOOST_REQUIRE ( rule1.isValid() );
    BOOST_REQUIRE ( rule2.isValid() );
    BOOST_REQUIRE ( rule3.isValid() );
    db.insert("campaign", rule1, true);
    db.insert("campaign", rule2, true);
    db.insert("campaign", rule3, true);

    Campaign::loadAll();
    Campaign campaign1("ADV-0001");
    Campaign campaign2("ADV-0002");
    Campaign campaign3("ADV-0003");

    {
	Rules rules;
	rules.set_country("UA");
	l = rules.campaigns();
	BOOST_CHECK_MESSAGE(!contains(l, campaign1), "GeoTargeting failed" );
	BOOST_CHECK_MESSAGE( contains(l, campaign2), "GeoTargeting failed" );
    }
    {
	Rules rules;
	rules.set_country("RU");
	l = rules.campaigns();
	BOOST_CHECK_MESSAGE( contains(l, campaign1), "GeoTargeting failed" );
	BOOST_CHECK_MESSAGE( contains(l, campaign2), "GeoTargeting failed" );
    }
    {
	Rules rules;
	rules.set_ip("95.69.248.16");		// Харьковский ip
	l = rules.campaigns();
	BOOST_CHECK_MESSAGE( contains(l, campaign3), "Region Targeting failed");
    }
    {
	Rules rules;
	rules.set_ip("127.0.0.1");
	l = rules.campaigns();
	BOOST_CHECK_MESSAGE(!contains(l, campaign3), "Region Targeting failed");
    }
}


/** Проверка ограничений дней недели */
BOOST_FIXTURE_TEST_CASE( TestWeekDays, F )
{
    BSONObj rule1 = fromjson(
	    "{  guid: 'ADV-0001', "
	    "   showConditions: { daysOfWeek: [1,2,3,4,5] }}"
	    );
    BSONObj rule2 = fromjson(
	    "{  guid: 'ADV-0002', "
	    "   showConditions: { daysOfWeek: [] }}"
	    );
    BOOST_REQUIRE ( rule1.isValid() );
    BOOST_REQUIRE ( rule2.isValid() );
    db.insert("campaign", rule1, true);
    db.insert("campaign", rule2, true);
    Campaign::loadAll();
    Campaign campaign1("ADV-0001");
    Campaign campaign2("ADV-0002");

    {
	ptime monday = time_from_string("2010-06-21 00:00:00");
	Rules rules;
	rules.set_time(monday);
	l = rules.campaigns();
	BOOST_CHECK_MESSAGE( contains(l, campaign1), "Days of week failed" );
	BOOST_CHECK_MESSAGE( contains(l, campaign2), "Days of week failed" );
    }
    {
	ptime sunday = time_from_string("2010-06-20 00:00:00");
	Rules rules;
	rules.set_time(sunday);
	l = rules.campaigns();
	BOOST_CHECK_MESSAGE(!contains(l, campaign1), "Days of week failed" );
	BOOST_CHECK_MESSAGE( contains(l, campaign2), "Days of week failed" );
    }
}

/** Проверка ограничений времени суток */
BOOST_FIXTURE_TEST_CASE( TestTimeOfDay, F )
{
    BSONObj rule1 = fromjson(
	    "{ guid: 'ADV-0001',                                           "
	    "showConditions: {                                             "
	    "   startShowTime: {hours: 7, minutes: 0},                     "
	    "   endShowTime: {hours: 23, minutes: 0}                       "
	    "}}"
	    );
    BSONObj rule2 = fromjson(
	    "{ guid: 'ADV-0002',                                           "
	    "showConditions: {                                             "
	    "   startShowTime: {hours: 0, minutes: 0},                     "
	    "   endShowTime: {hours: 0, minutes: 0}                        "
	    "}}"
	    );
    BOOST_REQUIRE ( rule1.isValid() );
    BOOST_REQUIRE ( rule2.isValid() );
    db.insert("campaign", rule1, true);
    db.insert("campaign", rule2, true);
    Campaign::loadAll();
    Campaign campaign1("ADV-0001");
    Campaign campaign2("ADV-0002");


    {
	ptime day = time_from_string("2010-06-21 12:00:00.000");
	Rules rules;
	rules.set_time(day);
	l = rules.campaigns();
	BOOST_CHECK_MESSAGE( contains(l, campaign1), "Time targeting failed" );
	BOOST_CHECK_MESSAGE( contains(l, campaign2), "Time targeting failed" );
    }
    {
	ptime night = time_from_string("2010-06-21 23:30:00.000");
	Rules rules;
	rules.set_time(night);
	l = rules.campaigns();
	BOOST_CHECK_MESSAGE(!contains(l, campaign1), "Time targeting failed" );
	BOOST_CHECK_MESSAGE( contains(l, campaign2), "Time targeting failed" );
    }
}


/** Проверка ограничений выбранными информерами, доменами и
    аккаунтами GetMyAd */
BOOST_FIXTURE_TEST_CASE( TestAllowedAndIgnoredInformers, F )
{
    BSONObj rule1 = fromjson(
	"{guid: 'ADV-0001',                                            "
	"showConditions: {                                             "
	"   showCoverage: 'allowed',				       "
	"   allowed: { accounts: ['account 1'],                        "
	"              domains:  ['domain 3', 'domain 4'],             "
	"              informers: ['INF#1']                            "
	"            }                                                 "
	"}}");
    BSONObj rule2 = fromjson(
	"{guid: 'ADV-0002',                                            "
	"showConditions: {                                             "
	"   showCoverage: 'all'					       "
	"}}");
    BSONObj rule3 = fromjson(
	    "{guid: 'ADV-0003',                                        "
	    "showConditions: {                                         "
	    "   showCoverage: 'all',				       "
	    "   ignored: { accounts: ['account 1'],                    "
	    "              domains:  ['domain 3', 'domain 4'],         "
	    "              informers: ['INF#1']                        "
	    "            }                                             "
	    "}}");
    BSONObj informer1 = fromjson(
	    "{guid: 'INF#1', user: 'xxx-account', domain: 'xxx-domain'}");
    BSONObj informer2 = fromjson(
	    "{guid: 'INF#2', user: 'account 1', domain: 'xxx-domain'}");
    BSONObj informer3 = fromjson(
	    "{guid: 'INF#3', domain: 'domain 3', user: 'xxx-account'}");
    BSONObj informer4 = fromjson(
	    "{guid: 'INF#4', domain: 'xxx-domain', account: 'xxx-account'}");

    BOOST_REQUIRE ( rule1.isValid() );
    BOOST_REQUIRE ( rule2.isValid() );
    BOOST_REQUIRE ( informer1.isValid() );
    BOOST_REQUIRE ( informer2.isValid() );
    BOOST_REQUIRE ( informer3.isValid() );
    BOOST_REQUIRE ( informer4.isValid() );

    db.insert("campaign", rule1, true);
    db.insert("campaign", rule2, true);
    db.insert("campaign", rule3, true);
    db.insert("informer", informer1, true);
    db.insert("informer", informer2, true);
    db.insert("informer", informer3, true);
    db.insert("informer", informer4, true);

    Campaign::loadAll();
    Informer::loadAll();
    Campaign campaign1("ADV-0001");
    Campaign campaign2("ADV-0002");
    Campaign campaign3("ADV-0003");

    {	// Уровень информеров
	Rules rules;
	rules.set_informer(Informer("INF#1"));
	l = rules.campaigns();
	BOOST_CHECK_MESSAGE( contains(l, campaign1), "Informer level tests");
	BOOST_CHECK_MESSAGE( contains(l, campaign2), "Informer level tests");
	BOOST_CHECK_MESSAGE(!contains(l, campaign3), "Informer level tests");
    }
    {	// Уровень аккаунтов
	Rules rules;
	rules.set_informer(Informer("INF#2"));
	l = rules.campaigns();
	BOOST_CHECK_MESSAGE( contains(l, campaign1), "Account level tests");
	BOOST_CHECK_MESSAGE( contains(l, campaign2), "Account level tests");
	BOOST_CHECK_MESSAGE(!contains(l, campaign3), "Account level tests");
    }
    {	// Уровень доменов
	Rules rules;
	rules.set_informer(Informer("INF#3"));
	l = rules.campaigns();
	BOOST_CHECK_MESSAGE( contains(l, campaign1), "Domain level tests");
	BOOST_CHECK_MESSAGE( contains(l, campaign2), "Domain level tests");
	BOOST_CHECK_MESSAGE(!contains(l, campaign3), "Domain level tests");
    }
    {	// Информер, которого нет в правилах
	Rules rules;
	rules.set_informer(Informer("INF#4"));
	l = rules.campaigns();
	BOOST_CHECK_MESSAGE(!contains(l, campaign1), "Defaults tests");
	BOOST_CHECK_MESSAGE( contains(l, campaign2), "Defaults tests");
	BOOST_CHECK_MESSAGE( contains(l, campaign3), "Defaults tests");
    }
}


/** Проверка показа кампании на тематических площадках. */
BOOST_FIXTURE_TEST_CASE( TestThematicShowCoverage, F )
{
    BSONObj campaign1_object = fromjson(
	"{guid: 'ADV-0001',                                            "
	"showConditions: {                                             "
	"   showCoverage: 'thematic',				       "
	"   categories: ['cat1', 'cat2']                               "
	"}}");
    BSONObj campaign2_object = fromjson(
	"{guid: 'ADV-0002',                                            "
	"showConditions: {                                             "
	"   showCoverage: 'thematic',				       "
	"   categories: ['cat3']                                       "
	"}}");
    BSONObj informer1_object = fromjson(
	"{guid: 'INF-0001',					       "
	"domain: 'example1.com'					       "
	"}");
    BSONObj informer2_object = fromjson(
	"{guid: 'INF-0002',					       "
	"domain: 'example2.com'					       "
	"}");
    BSONObj domain_category1_object = BSON(
	    "domain" << "example1.com" <<
	    "categories" << BSON_ARRAY("cat1" << "cat3"));
    BSONObj domain_category2_object = BSON(
	    "domain" << "example2.com" <<
	    "categories" << BSON_ARRAY("cat1"));


    db.insert("campaign", campaign1_object, true);
    db.insert("campaign", campaign2_object, true);
    db.insert("informer", informer1_object, true);
    db.insert("informer", informer2_object, true);
    db.insert("domain.categories", domain_category1_object, true);
    db.insert("domain.categories", domain_category2_object, true);

    Campaign::loadAll();
    Informer::loadAll();
    Campaign campaign1("ADV-0001");
    Campaign campaign2("ADV-0002");

    BOOST_REQUIRE_EQUAL(Informer("INF-0001").categories().size(), 2);
    BOOST_REQUIRE_EQUAL(Informer("INF-0002").categories().size(), 1);

    {
	Rules rules;
	rules.set_informer(Informer("INF-0001"));
	l = rules.campaigns();
	BOOST_CHECK( contains(l, campaign1) );
	BOOST_CHECK( contains(l, campaign2) );
    }
    {
	Rules rules;
	rules.set_informer(Informer("INF-0002"));
	l = rules.campaigns();
	BOOST_CHECK( contains(l, campaign1) );
	BOOST_CHECK(!contains(l, campaign2) );
    }
}


/** Проверка, что при если есть хотя бы одна подходящая коммерческая
    кампании, то социальные будут исключены из показа.

    Тест на пользовательские заглушки см. в test_core. */
BOOST_FIXTURE_TEST_CASE( TestSocial, F )
{
    // Коммерческая кампания с таргетингом на Россию
    BSONObj rule1 = fromjson(
	    "{guid:  'ADV-0001',                                           "
	    "social: false,	                                           "
	    "showConditions: {                                             "
	    "	geoTargeting: ['RU']                                       "
	    "}}");

    // Социальная реклама для показа во всех странах
    BSONObj rule2 = fromjson(
	    "{guid:  'ADV-0002',                                           "
	    "social: true,	                                           "
	    "showConditions: {                                             "
	    "	geoTargeting: []				           "
	    "}}");

    BOOST_REQUIRE ( rule1.isValid() );
    BOOST_REQUIRE ( rule2.isValid() );
    db.insert("campaign", rule1, true);
    db.insert("campaign", rule2, true);

    Campaign::loadAll();
    Campaign campaign1("ADV-0001");
    Campaign campaign2("ADV-0002");

    {	// 1. Для России должна показаться только коммерческая кампания
	Rules rules;
	rules.set_country("RU");
	l = rules.campaigns();
	BOOST_CHECK_MESSAGE( contains(l, campaign1),
			    "Social campaigns test failed");
	BOOST_CHECK_MESSAGE(!contains(l, campaign2),
			    "Social campaigns test failed");
    }
    {	// 2. Для других стран должна показываться только социальная реклама
	Rules rules;
	rules.set_country("UA");
	l = rules.campaigns();
	BOOST_CHECK_MESSAGE(!contains(l, campaign1),
			    "Social campaigns test failed");
	BOOST_CHECK_MESSAGE( contains(l, campaign2),
			    "Social campaigns test failed");
    }

}


/** Проверка, что на информерах, принадлежащих заблокированным аккаунтам,
    показывается только социальная реклама */
BOOST_FIXTURE_TEST_CASE( TestBlockedInformers, F )
{
    // Коммерческая кампания
    BSONObj rule1 = fromjson(
	    "{guid:  'ADV-0001',                                           "
	    "social: false,	                                           "
	    "showConditions: {showCoverage: 'all'}                         "
	    "}");

    // Социальная реклама
    BSONObj rule2 = fromjson(
	    "{guid:  'ADV-0002',                                           "
	    "social: true,	                                           "
	    "showConditions: {showCoverage: 'all'}                         "
	    "}");

    // Информер заблокированного пользователя
    BSONObj informerObj = fromjson("{guid: 'INF#1', user: 'blocked-account'}");
    BSONObj userObj = fromjson("{login: 'blocked-account', blocked: 'banned'}");

    BOOST_REQUIRE ( rule1.isValid() );
    BOOST_REQUIRE ( rule2.isValid() );
    BOOST_REQUIRE ( informerObj.isValid() );
    BOOST_REQUIRE ( userObj.isValid() );
    db.insert("campaign", rule1, true);
    db.insert("campaign", rule2, true);
    db.insert("informer", informerObj, true);
    db.insert("users", userObj, true);

    Campaign::loadAll();
    Informer::loadAll();
    Campaign campaign1("ADV-0001");
    Campaign campaign2("ADV-0002");
    Informer informer("INF#1");

    BOOST_REQUIRE( informer.valid() );
    BOOST_REQUIRE( informer.blocked() );

    {	// 1. На обычных информерах должна показываться коммерческая реклама
	Rules rules;
	l = rules.campaigns();
	BOOST_CHECK_MESSAGE( contains(l, campaign1),
			    "Blocked informers test failed (stage 1a)");
	BOOST_CHECK_MESSAGE(!contains(l, campaign2),
			    "Blocked informers test failed (stage 1b)");
    }
    {	// 2. На заблокированных информерах -- только социальная реклама
	Rules rules;
	rules.set_informer(informer);
	l = rules.campaigns();
	BOOST_CHECK_MESSAGE(!contains(l, campaign1),
			    "Blocked informers test failed (stage 2a)");
	BOOST_CHECK_MESSAGE( contains(l, campaign2),
			    "Blocked informers test failed (stage 2b)");
    }
}


/** Проверка определения страны по IP */
BOOST_AUTO_TEST_CASE( TestCountryDetection )
{
    Rules rules;
    rules.set_ip("95.69.248.219");
    BOOST_CHECK_EQUAL( rules.country(), "UA" );

    rules.set_ip("87.250.251.3");
    BOOST_CHECK_EQUAL( rules.country(), "RU" );

    rules.set_ip("invalid ip");
    BOOST_CHECK_EQUAL( rules.country(), "" );
}

BOOST_AUTO_TEST_SUITE_END()
