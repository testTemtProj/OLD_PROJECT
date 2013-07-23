#include <QFile>
#include <QDateTime>
#include <QTimer>
#include <QDebug>
#include "DictionaryManager.h"
#include "Exception.h"

DictionaryManager::DictionaryManager(QObject *parent) :
    QObject(parent)
{
    timerDictionaryChanged.setSingleShot(true);
    connect(&timerDictionaryChanged, SIGNAL(timeout()), this, SLOT(reloadDictionary()));
    connect(&watcher, SIGNAL(fileChanged(QString)), this, SLOT(dictionaryChanged(QString)));
}

DictionaryManager::~DictionaryManager()
{
    foreach (QSharedMemory *shared, data.values())
        delete shared;
    data.clear();
}


/** Слот вызывается каждый раз при изменении файла словаря на диске.

    Во время перезаписи файла сообщение об изменении отправляется несколько
    раз. Поэтому этот слот при каждом вызове откладывает реальное чтение. */
void DictionaryManager::dictionaryChanged(const QString &path)
{
    // Перезагружаем словарь
    //qDebug() << QString("dictionary changed signal recieved: %1.").arg(path);
    changedDictionaryPath = path;
    timerDictionaryChanged.start(500);
}

/** Перезагружает словарь по пути changedDictionaryPath */
void DictionaryManager::reloadDictionary()
{
    QString &path = changedDictionaryPath;
    qDebug() << QString("reloading dictionary from %1.").arg(path);
    try {
        QString key = filenameToKey.value(path);
        QSharedMemory *shared = data.value(key);
        if (!shared)
            throw Exception(QString("Ошибка перезагрузки словаря %1. Словарь не был загружен ранее.").arg(path));

        QFile fileDictionary(path);
        QByteArray buffer;
        if (!fileDictionary.open(QFile::ReadOnly))
            throw Exception(QString("Ошибка чтения файла словаря. Key: %1; file: %2").arg(key).arg(path));

        buffer = fileDictionary.readAll();
        shared->lock();
        char *to = (char *)shared->data();
        const char *from = buffer.data();
        memcpy(to, from, qMin(shared->size(), buffer.size()));
        shared->unlock();

        qDebug() << "Словарь обновлён";
    } catch (Exception &ex) {
        qDebug() << tr("Ошибка во время загрузки словаря %1.\nОписание: %2").arg(path).arg(ex.text());
    }
}


/*!
    Добавляет словарь
*/
void DictionaryManager::addDictionary(const QString &filename, const QString &key)
{
    QSharedMemory *shared = loadDictionary(filename, key);
    data[key] = shared;
    filenameToKey[filename] = key;
    watcher.addPath(filename);
    qDebug() << tr("Словарь %1 успешно загружен с ключём %2").arg(filename).arg(key);
}


/*!
    Возвращает true, если не было загружено ни одного словаря
*/
bool DictionaryManager::isEmpty() const
{
    return data.isEmpty();
}


/*!
  Загружает словарь из файла filename в разделяемую память с ключём key.
  */
QSharedMemory *DictionaryManager::loadDictionary(const QString &filename, const QString &key)
{
    QFile fileDictionary(filename);
    QByteArray buffer;
    QSharedMemory *shared;
    if (!fileDictionary.open(QFile::ReadOnly))
        throw Exception(QString("Ошибка чтения файла словаря. Key: %1; file: %2").arg(key).arg(filename));

    buffer = fileDictionary.readAll();
    shared = new QSharedMemory(key);
    if (!shared->create(buffer.size() * 1.2))   // Выделяем память с 20% запасом
        throw Exception(QString("Ошибка выделения памяти под словарь %1. Описание: %2. "
                               "Словарь будет пропущен.")
                           .arg(key)
                           .arg(shared->errorString()));
    shared->lock();
    char *to = (char *)shared->data();
    const char *from = buffer.data();
    memcpy(to, from, qMin(shared->size(), buffer.size()));
    shared->unlock();

    return shared;
}

