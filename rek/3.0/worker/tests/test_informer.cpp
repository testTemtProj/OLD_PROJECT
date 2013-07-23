#define BOOST_TEST_DYN_LINK
#include <boost/test/unit_test.hpp>

#include "../src/Informer.h"
#include "../src/DB.h"

using namespace mongo;


/** Заполняет базу данных тестовыми данными */
void CreateTestDatabase()
{
    DB db;
    db.dropDatabase();
    db.insert("informer",
	      BSON( "guid" << "inf#01" <<
		    "title" << "Informer #1" <<
		    "css" << ".informer-css {}" <<
		    "domain" << "example.com" <<
		    "user" << "test-user" <<
		    "admaker" << fromjson("{Main: {itemsNumber: 3}}") <<
		    "nonRelevant" << fromjson("{action: 'usercode',"
                                      "userCode: 'test user code'}")),
	      true /* safe */);
    db.insert("informer",
	      BSON( "guid" << "inf#02" <<
		    "title" << "Informer #2" <<
		    "css" << ".informer-css {}" <<
		    "domain" << "example.com" <<
		    "user" << "test-user" <<
		    "admaker" << fromjson("{Main: {itemsNumber: 3}}") <<
		    "nonRelevant" << fromjson("{action: 'usercode',"
                                      "userCode: 'test user code'}")),
	      true /* safe */);
    db.insert("domain.categories", BSON(
	    "domain" << "example.com" <<
	    "categories" << BSON_ARRAY("cat1" << "cat2")),
	      true /* safe */);
    db.insert("users", BSON(
	    "login" << "test-user" <<
	    "blocked" << "banned"),
	      true);
}


/** Проверка загрузки одного информера */
BOOST_AUTO_TEST_CASE( LoadOneInformer )
{
    CreateTestDatabase();
    Informer::invalidateAll();
    Informer informer1("inf#01");
    Informer informer2("inf#02");

    // Проверяем состояние информеров до загрузки
    BOOST_CHECK( informer1.valid() == false );
    BOOST_CHECK( informer2.valid() == false );

    // Загружаем один информер
    Informer::loadInformer(informer2);

    // Должен был загрузиться только informer2
    BOOST_CHECK( informer1.valid() == false );
    BOOST_CHECK( informer2.valid() == true );
}

/** Проверка загрузки информера из базы данных */
BOOST_AUTO_TEST_CASE( LoadAllInformers )
{
    CreateTestDatabase();
    Informer::invalidateAll();
    Informer informer("inf#01");
    Informer informer2("inf#02");

    // Проверяем состояние информеров до загрузки
    BOOST_CHECK( informer.valid() == false );
    BOOST_CHECK( informer2.valid() == false );
    BOOST_CHECK( informer.is_null() == false );
    BOOST_CHECK_EQUAL( informer.id(), "inf#01" );
    BOOST_CHECK_EQUAL( informer.domain(), "" );
    BOOST_CHECK_EQUAL( informer.title(), "" );
    BOOST_CHECK_EQUAL( informer.css(), "" );
    BOOST_CHECK_EQUAL( informer.user(), "" );
    BOOST_CHECK_EQUAL( informer.capacity(), 0);
    BOOST_CHECK_EQUAL( informer.categories().size(), 0);
    BOOST_CHECK_EQUAL( informer.nonrelevant(), Informer::Show_Social );
    BOOST_CHECK_EQUAL( informer.user_code(), "" );
    BOOST_CHECK_EQUAL( informer.blocked(), false );

    // Загружем все информеры и проверяем состояние после загрузки
    Informer::loadAll();
    BOOST_CHECK( informer.valid() == true );
    BOOST_CHECK( informer2.valid() == true );
    BOOST_CHECK_EQUAL( informer.id(), "inf#01" );
    BOOST_CHECK_EQUAL( informer.domain(), "example.com" );
    BOOST_CHECK_EQUAL( informer.title(), "Informer #1" );
    BOOST_CHECK_EQUAL( informer.css(), ".informer-css {}" );
    BOOST_CHECK_EQUAL( informer.user(), "test-user" );
    BOOST_CHECK_EQUAL( informer.capacity(), 3);
    BOOST_CHECK_EQUAL( informer.blocked(), true );
    std::set<std::string> test_set_categories;
    test_set_categories.insert("cat1");
    test_set_categories.insert("cat2");
    BOOST_CHECK( informer.categories() == test_set_categories );
    BOOST_CHECK_EQUAL( informer.nonrelevant(), Informer::Show_UserCode );
    BOOST_CHECK_EQUAL( informer.user_code(), "test user code" );
}


/** Проверка свойств информера null и invalid */
BOOST_AUTO_TEST_CASE(TestInformerNullInvalid)
{
    {
	Informer null;
	BOOST_CHECK(null.is_null() == true);
	BOOST_CHECK(null.valid() == false);
    }
    {
	Informer invalid("INVALID");
	BOOST_CHECK(invalid.is_null() == false);
	BOOST_CHECK(invalid.valid() == false);
    }
}


/** Проверка нечувствительности к регистру в id информера */
BOOST_AUTO_TEST_CASE(TestInformerCaseInsensitive)
{
    DB db;
    db.dropDatabase();
    db.insert("informer",
	      BSON("guid" << "InF #01" <<
		   "title" << "test informer"),
	      true);
    Informer::loadAll();

    BOOST_CHECK(Informer("InF #01").valid());
    BOOST_CHECK(Informer("inf #01").valid());
    BOOST_CHECK(Informer("INF #01").valid());
}
