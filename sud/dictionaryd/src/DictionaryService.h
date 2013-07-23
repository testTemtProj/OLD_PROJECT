#ifndef DICTIONARYSERVICE_H
#define DICTIONARYSERVICE_H

#include <QtCore/QCoreApplication>
#include <QtCore/QTextStream>
#include <QtCore/QSettings>
#include <QSharedMemory>
#include <QDomDocument>
#include <QTextCodec>
#include <QFile>
#include <QDebug>
#include <QDateTime>
#include "qtservice.h"
#include "DictionaryManager.h"


class DictionaryService : public QtService<QCoreApplication>
{
public:
    DictionaryService(int argc, char **argv);
    virtual ~DictionaryService();

protected:
    void start();
    void stop();

private:
    DictionaryManager *manager;
};


#endif // DICTIONARYSERVICE_H
