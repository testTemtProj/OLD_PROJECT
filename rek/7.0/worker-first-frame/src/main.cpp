#include <glog/logging.h>
#include "CgiService.h"

/** \mainpage GetMyAd first frame worker
 *
    Сервис использует следующие get-параметры, передаваемые в URL:

    \param scr      id информера, на котором осуществляется показ рекламы.
		            В основном (рабочем) режиме, это единственный обязательный
		            параметр.

    \param location адрес страницы, на которой расположен информер. Обычно
            		передаётся из javascript загрузчика.

    \param referrer адрес страницы, с которой посетитель попал на сайт-партнёр.
            		Обычно передаётся из javascript загрузчика.

*/


int main(int argc, char *argv[])
{
    google::InitGoogleLogging(argv[0]);
    CgiService(argc, argv).Serve();
    return 0;
}
