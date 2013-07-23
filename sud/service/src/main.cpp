/*
 * FastCGI-сервис подсказок.
 * Дата модификации: 2009-07-01
 *
 *
 * Принимаемые параметры:
 * 		q - начало запроса, для которого нужно выдать подсказку (в percent encoded Utf-8)
 *
 */

#include <QtCore>
#include <glog/logging.h>
#include "fcgi_stdio.h"
#include "SuggestService.h"

extern char **environ;

void GlogHandler(QtMsgType type, const char *msg)
{
    switch (type) {
    case QtDebugMsg:
        LOG(INFO) << msg;
        break;
    case QtWarningMsg:
        LOG(WARNING) << msg;
        break;
    case QtCriticalMsg:
        LOG(ERROR) << msg;
        break;
    case QtFatalMsg:
        LOG(ERROR) << "Fatal: " << msg;
        abort();
    }
}


int main(int argc, char **argv)
{
    QCoreApplication a(argc, argv);
    QTextCodec::setCodecForTr(QTextCodec::codecForName("UTF-8"));
    QTextCodec::setCodecForCStrings(QTextCodec::codecForName("UTF-8"));
    qApp->addLibraryPath(qApp->applicationDirPath());
    google::InitGoogleLogging(argv[0]);
    qInstallMsgHandler(GlogHandler);

    SuggestService service;
    if (!service.init(argc, argv))
        return 1;
    else {
        LOG(INFO) << "SuggestService " << service.version() << " init ok";
    }

    while (FCGI_Accept() >= 0) {
        // Разрешаем заменить строку запроса параметром командной строки
        QString queryString = getenv("QUERY_STRING");
        if (queryString.isEmpty()) {
            for (int i = 1; i < argc; i++)
                if (QString(argv[i]).startsWith("q="))
                    queryString = argv[i];
        }

        QString result = service.processQuery(queryString);

        printf(	"Content-Type: text/html; charset=\"utf-8\"\r\n"
                "\r\n");
        printf("%s", result.toUtf8().data());
    }
}

