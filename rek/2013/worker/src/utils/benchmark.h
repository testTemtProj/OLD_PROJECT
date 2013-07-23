#ifndef BENCHMARK_H
#define BENCHMARK_H

#include <string>
#include <boost/date_time/posix_time/ptime.hpp>
#include <glog/logging.h>

class Benchmark {
public:
    Benchmark(const std::string &message)
        : message_(message),
          start_(boost::posix_time::microsec_clock::local_time())
    {}

    ~Benchmark()
    {
        long elapsed = 
            (boost::posix_time::microsec_clock::local_time() - start_)
            .total_milliseconds();
        LOG(INFO) << message_ << " (" << elapsed << " ms)";
    }

private:
    std::string message_;
    boost::posix_time::ptime start_;
};

#endif 

