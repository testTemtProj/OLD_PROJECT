#define BOOST_TEST_DYN_LINK
#define BOOST_TEST_MAIN

#include <boost/test/unit_test.hpp>
#include <glog/logging.h>
#include "../src/DB.h"

struct GlobalInit {
    GlobalInit()
    {
	google::InitGoogleLogging("getmyad-worker");
	mongo::DB::addDatabase("localhost", "test", false);
    }
};

BOOST_GLOBAL_FIXTURE( GlobalInit );

