#include <QDir>
#include <signal.h>

#include "Exception.h"
#include "DictionaryService.h"


void LogToFile(const char *filename, const char *msg, const char *level)
{
    QFile f(filename);
    if (!f.open(QFile::Append))
        return;
    f.write(QDateTime::currentDateTime().toString().toAscii());
    f.write("\t");
    f.write(msg);
    f.write("\n");
}


void myMessageOutput(QtMsgType type, const char *msg)
{
    switch (type) {
    case QtDebugMsg:
        LogToFile("/tmp/dictionaryd.log", msg, "DEBUG");
        break;

    case QtWarningMsg:
        fprintf(stderr, "Warning: %s\n", msg);
        LogToFile("/tmp/dictionaryd.log", msg, "WARNING");
        break;
    case QtCriticalMsg:
        fprintf(stderr, "Critical: %s\n", msg);
        LogToFile("/tmp/dictionaryd.log", msg, "CRITITCAL");
        break;
    case QtFatalMsg:
        fprintf(stderr, "Fatal: %s\n", msg);
        LogToFile("/tmp/dictionaryd.log", msg, "FATAL");
        abort();
    }
}

DictionaryService *service = 0;

void CtrlC_Handler(int)
{
    myMessageOutput(QtDebugMsg, "Terminating service by Ctrl-C");
    delete service;
    exit(0);
}


int main(int argc, char **argv)
{
    QTextCodec::setCodecForTr(QTextCodec::codecForName("UTF-8"));
    QTextCodec::setCodecForLocale(QTextCodec::codecForName("UTF-8"));
    QTextCodec::setCodecForCStrings(QTextCodec::codecForName("UTF-8"));
    qInstallMsgHandler(myMessageOutput);
#if !defined(Q_WS_WIN)
    // QtService stores service settings in SystemScope, which normally
    // require root privileges.
    // To allow testing this example as non-root, we change the directory
    // of the SystemScope settings file.
    QSettings::setPath(
        QSettings::NativeFormat,
        QSettings::SystemScope,
        QDir::tempPath());
#endif

    signal(SIGINT, CtrlC_Handler);
    service = new DictionaryService(argc, argv);
    return service->exec();
}

