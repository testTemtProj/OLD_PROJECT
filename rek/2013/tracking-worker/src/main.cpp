#include <glog/logging.h>
#include "CgiService.h"

/** \mainpage GetMyAd tracking worker
 
    \section usage_section Использование
*/


int main(int argc, char *argv[])
{
    google::InitGoogleLogging(argv[0]);
    CgiService(argc, argv).Serve();
    return 0;
}
