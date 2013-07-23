/*
 * TrieCompiled.h
 *
 *  Created on: 11.09.2009
 *      Author: Silver
 */

#ifndef TRIECOMPILED_H_
#define TRIECOMPILED_H_

#include <QtCore>
#include "TrieCompiled.h"
#include "TrieCompiledNode.h"

class TrieCompiled {
public:
    TrieCompiled(const char *buffer = 0);
    TrieCompiled(const QString &filename);

    virtual ~TrieCompiled();

    void setBuffer(const char *buffer);
    const char *buffer() const;

    QList<TrieCompiledNode *> searchPattern(const QString &pattern);

    /** Возвращает мета-данные словаря, ассоциированные с ключём \a key */
    QByteArray metaData(const QString &key) const;

    /** Устанавливает мета-данные *в памяти*. В файл словаря эти мета-данные
     *  сохранены не будут! */
    void setMetaData(const QString &key, const QByteArray &value);
    void setMetaData(const QString &key, const QString &value);

private:

    typedef QMap<QString, QByteArray> MetaDataMap;

    struct State {
        enum Pattern {
            AnyChar,
            OneOfSet
        }           pattern;
        quint32     nodeOffset;
        quint8      chainIndex;
        int         child_number;
        int         pos;
        char        char_set[5];
        short       char_set_len;
    };

    const char *m_buffer;        // Указатель на начало словаря
    const char *m_dataStart;     // Указатель на начало области данных в словаре
    QByteArray tempBuffer;
    MetaDataMap m_metaData;

    MetaDataMap _readMetaData(const char *ptrMetaData);
};

#endif /* TRIECOMPILED_H_ */
