#include <boost/test/unit_test.hpp>
#define private public
#include "../src/CgiService.h"
#undef private

BOOST_AUTO_TEST_CASE( TestGetEnv )
{
    CgiService service(0, 0);
    std::string path = service.getenv("PATH", "");
    BOOST_CHECK( !path.empty() );

    std::string default_value = service.getenv("ImNotExist", "default");
    BOOST_CHECK( default_value == "default" );
}

