#include <boost/test/unit_test.hpp>
#include "../src/utils/UrlParser.h"
#include "../src/utils/base64.h"
#include "../src/utils/GeoIPTools.h"

/** Проверка выделения параметров из полного URL */
BOOST_AUTO_TEST_CASE( TestQueryParameters )
{
    UrlParser url("http://example.com/a/test?q=123&loc=kharkiv&p3=333");

    BOOST_CHECK_EQUAL( url.params().size(), 3 );
    BOOST_CHECK_EQUAL( url.param("q"), "123" );
    BOOST_CHECK_EQUAL( url.param("loc"), "kharkiv" );
    BOOST_CHECK_EQUAL( url.param("p3"), "333" );
}


/** Проверка неполного URL */
BOOST_AUTO_TEST_CASE( TestIncompleteUrl )
{
    UrlParser url("q=123&loc=kharkiv&p3=333");

    BOOST_CHECK_EQUAL( url.params().size(), 3 );
    BOOST_CHECK_EQUAL( url.param("q"), "123" );
    BOOST_CHECK_EQUAL( url.param("loc"), "kharkiv" );
    BOOST_CHECK_EQUAL( url.param("p3"), "333" );
}

/** Проверка параметров, содержащих экранированные символы */
BOOST_AUTO_TEST_CASE( TestParametersWithEscapeChars )
{
    UrlParser url("http://example.com?q=bmw%20x5%20%26%20others%20100%25");

    BOOST_CHECK_EQUAL( url.param("q"), "bmw x5 & others 100%");
}

/** Проверка параметров, содержащих некорректно экранированные символы */
BOOST_AUTO_TEST_CASE( TestParametersWithBrokenEscapeChars )
{
    UrlParser url("http://example.com?q=bmw%2%x5%20%26%20others");

    BOOST_CHECK_EQUAL( url.param("q"), "bmw%2%x5 & others");
}


/** Проверка безопасного для url Base64 кодирования и декодирования */
BOOST_AUTO_TEST_CASE( TestBase64 )
{
    std::string s = "<a href=\"http://example.com\">Hello world!</a>\t";
    std::string base64 = "PGEgaHJlZj0iaHR0cDovL2V4YW1wbGUuY29tIj5IZWxsbyB3b3JsZ"
			 "CE8L2E-CQ==";
    BOOST_CHECK_EQUAL( base64_encode(s), base64 );
    BOOST_CHECK_EQUAL( base64_decode(base64), s );
}


/** Проверка определения страны и областей по ip */
BOOST_AUTO_TEST_CASE( TestGeoIP )
{
    std::string ip = "95.69.248.16";
    BOOST_CHECK_EQUAL( country_code_by_addr(ip), "UA" );
    BOOST_CHECK_EQUAL( region_code_by_addr(ip), "Kharkivs'ka Oblast'" );
}

