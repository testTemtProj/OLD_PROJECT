#include <QDebug>

#include "DictionaryService.h"
#include "Exception.h"

DictionaryService::DictionaryService(int argc, char **argv)
        : QtService<QCoreApplication>(argc, argv, "dictionaryd"),
        manager(0)
{
    setServiceDescription("Stores Yottos Suggest Dictionary in shared memory");
    //setServiceFlags(QtServiceBase::CanBeSuspended);
}


DictionaryService::~DictionaryService()
{
    stop();
}

/*!
  Запуск службы.
  */
void DictionaryService::start()
{
    qDebug() << "Starting service...";

    QCoreApplication *app = application();
    manager = new DictionaryManager(app);
    QDomDocument xmlSettings;
    QFile fileSettings(app->applicationDirPath() + "/settings.xml");
    if (!fileSettings.open(QFile::ReadOnly)) {
        qCritical() << "Ошибка чтения файла настроек" <<
                    (app->applicationDirPath() + "/settings.xml");
        app->quit();
        return;
    }

    QString errorMessage;
    if (!xmlSettings.setContent(&fileSettings, &errorMessage)) {
        qCritical() << "Неверный формат файла настроек settings.xml: " <<
                    errorMessage;
        app->quit();
        return;
    }

    QDomElement elDictionary = xmlSettings.documentElement()
                                          .firstChildElement("Dictionary");
    while (!elDictionary.isNull())
    {
        QString key = elDictionary.firstChildElement("key").text();
        QString file = elDictionary.firstChildElement("file").text();

        try {
            manager->addDictionary(file, key);
        } catch (Exception& ex) {
            qCritical() << ex.text();
        }

        elDictionary = elDictionary.nextSiblingElement("Dictionary");
    }

    if (manager->isEmpty()) {
        qCritical() << "Не загружено ни одного словаря!";
        app->quit();
        return;
    }
}


void DictionaryService::stop()
{
    qDebug() << "Stopping service...";
    if (manager)
        delete manager;
}



