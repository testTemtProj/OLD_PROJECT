#ifndef DICTIONARYMANAGER_H
#define DICTIONARYMANAGER_H

#include <QObject>
#include <QFileSystemWatcher>
#include <QString>
#include <QSharedMemory>
#include <QMap>
#include <QTimer>



class DictionaryManager : public QObject
{
Q_OBJECT
public:
    explicit DictionaryManager(QObject *parent = 0);
    virtual ~DictionaryManager();

    void addDictionary(const QString &filename, const QString &key);
    bool isEmpty() const;

signals:

public slots:
    void dictionaryChanged(const QString &path);
    void reloadDictionary();

private:
    QSharedMemory *loadDictionary(const QString &filename, const QString &key);

    QFileSystemWatcher watcher;
    QMap<QString, QSharedMemory*> data;                     // key -> dictionary
    QMap<QString, QSharedMemory*> dataVersion;              // key -> dictionary version
    QMap<QString, QString> filenameToKey;                   // filename => key
    QTimer timerDictionaryChanged;
    QString changedDictionaryPath;
};

#endif // DICTIONARYMANAGER_H
