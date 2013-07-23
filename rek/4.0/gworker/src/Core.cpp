#include "DB.h"
#include <boost/foreach.hpp>
#include <boost/date_time/posix_time/ptime.hpp>
#include <boost/date_time/posix_time/posix_time_io.hpp>
#include <boost/format.hpp>
#include <boost/algorithm/string.hpp>
#include <glog/logging.h>
#include <ctime>
#include <cstdlib>
#include <sstream>
#include <mongo/util/version.h>
#include <mongo/bson/bsonobjbuilder.h>

#include "Core.h"
#include "GuaranteedDisplayTemplate.h"
#include "utils/base64.h"
#include "utils/benchmark.h"


using std::list;
using std::vector;
using std::map;
using std::unique_ptr;
using namespace boost::posix_time;
#define foreach	BOOST_FOREACH

Core::Core()
{
    InitMongoDB();
}

Core::~Core()
{
}

std::string Core::Process(const Core::Params &params)
{
    mongo::DB db("log");

    std::tm dt_tm;
    dt_tm = boost::posix_time::to_tm(params.time_);
    mongo::Date_t dt( (mktime(&dt_tm)) * 1000LLU);

    mongo::BSONObj record = mongo::BSONObjBuilder().genOID().
	append("dt", dt).
	append("inf", params.informer_).
	append("ip", params.ip_).
	obj();

    db.insert("log.impressions", record, true);

    return boost::str(boost::format(GuaranteedDisplayTemplate()));
}

/** Подготовка базы данных MongoDB.
*/
void Core::InitMongoDB()
{
    mongo::DB db("log");
    const int K = 1000;
    const int M = 1000 * K;
    db.createCollection("log.impressions", 250*M, true, 1*M);
}
