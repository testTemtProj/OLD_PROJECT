#define BOOST_TEST_DYN_LINK
#include <boost/test/unit_test.hpp>
#include <glog/logging.h>
#include "../src/DB.h"

using namespace mongo;


/** Проверка параметров обёртки над mongodb. */
BOOST_AUTO_TEST_CASE ( TestMongoWrapper )
{
    // База данных по умолчанию уже подготовлена в GlobalInit (localhost, test)
    BOOST_CHECK_NO_THROW(new DB());

    // А эта база данных ещё не зарегистрирована
    BOOST_CHECK_THROW(new DB("logdb"), DB::NotRegistered);

    DB::addDatabase("logdb", "127.0.0.1", "log_database", false);

    DB db_main;
    DB db_log("logdb");

    BOOST_CHECK_EQUAL( db_main.server_host(), "localhost" );
    BOOST_CHECK_EQUAL( db_main.database(), "test" );
    BOOST_CHECK_EQUAL( db_log.server_host(), "127.0.0.1" ) ;
    BOOST_CHECK_EQUAL( db_log.database(), "log_database" );

    BOOST_CHECK_EQUAL(db_main.collection("my.coll"), "test.my.coll");
}


/** Проверка операций с базой данных (mongodb) */
BOOST_AUTO_TEST_CASE ( TestMongoOperations )
{
    DB db;
    db.dropCollection("people");

    BOOST_CHECK( db.count("people") == 0 );

    db.insert("people", BSON( "name" << "silver" << "age" << 25 ));
    db.insert("people", BSON( "name" << "maori" << "age" << 24 ));
    db.insert("people", BSON( "name" << "unknown" << "age" << 0 ));
    BOOST_CHECK( db.count("people") == 3 );

    BSONObj obj = db.findOne("people", QUERY("name" << "maori"));
    BOOST_CHECK( obj.isValid() );
    BOOST_CHECK_EQUAL( obj.getStringField("name"), "maori" );
    BOOST_CHECK_EQUAL( obj.getIntField("age"), 24 );

    db.remove("people", QUERY("age" << 0));
    BOOST_CHECK( db.count("people") == 2 );
}


/** Проверка на множественные одновременные подключения из пула */
BOOST_AUTO_TEST_CASE ( TestConnectionPool )
{
    {
	// Открываем 100 подключений к базе данных
	std::vector<DB *> connections;
	for (int i = 0; i < 150; i++) {
	    DB *db =  new DB();
	    connections.push_back(db);
	}
	for (size_t i = 0; i < connections.size(); i++)
	    delete connections[i];
    }
}


/** Тест вспомогательной функции, которая пытается пребразовать поле
    базы данных в int */
BOOST_AUTO_TEST_CASE( TestFieldToInt )
{
    DB db;
    db.dropCollection("test_int");
    db.insert("test_int", BSON("str" << "42" <<
                               "int" << 84 <<
                               "bad" << "asdf"));
    BSONObj x = db.findOne("test_int", Query());
    BOOST_CHECK_EQUAL( DB::toInt(x["str"]), 42);
    BOOST_CHECK_EQUAL( DB::toInt(x["int"]), 84);
    BOOST_CHECK_EQUAL( DB::toInt(x["bad"]), 0);
    BOOST_CHECK_EQUAL( DB::toInt(x["not_exists"]), 0);
}

