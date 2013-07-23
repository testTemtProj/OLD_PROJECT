/*
 * TrieCompiledNode.h
 *
 *  Created on: 11.09.2009
 *      Author: Silver
 */

#ifndef TRIECOMPILEDNODE_H_
#define TRIECOMPILEDNODE_H_

#include <QtCore>

class TrieCompiledNode {
public:
    TrieCompiledNode();
    TrieCompiledNode(const char *buffer, quint32 offset, quint8 chainIndex = 0);
    TrieCompiledNode(QDataStream *data, quint32 offset);
    virtual ~TrieCompiledNode();

    enum NodeType {
        Terminator = 0,
        OneChar = 1,
        Chain = 2
    };

    enum NodeFlags {
        HasData = 16,
        ShortOffset = 32,
        ChainTerminated = 64,
        ChainSameData = 128
    };


    QList<TrieCompiledNode*> descents(const QList <quint8> &stopSymbols = (QList<quint8>() << '$'));
    QList<TrieCompiledNode*> completeWord();

    QString userData();
    const quint8 *userDataPtr(int *len);

    bool iterateToChild(char c);
    bool iterateToChildIndex(int index);
    bool setOffset(quint32 offset, quint8 chainIndex = 0);
    quint32 offset() const;
    QString fullPath() const;
    quint8 value() const;
    NodeType type() const;
    TrieCompiledNode parent() const;

    quint8 getChainIndex() const { return chainIndex; }
    const char *getHeaderPointer() const { return p; }

    bool equals(TrieCompiledNode *other) const;


private:
    const char *p;              /// Указатель на заголовок узла
    const char *buffer;         /// Указатель на скомпилированный словарь

    quint8 header() const;
    quint8 childCount() const;
    quint8 chainLength() const;
    quint32 parentOffset() const;
    quint8 parentIndex() const;

    quint8 chainIndex;
    quint8 nodeValue;

    quint32 childOffset(int index) const;
    quint8 childIndex(int index) const;
    quint32 skipChainNode();

};


typedef QList<TrieCompiledNode*> node_list;

/*!
    Читает целое число, расположенное по адресу src.

    Допустимые типы: qint16, qint32, qint64, а также quint16, quint32, quint64.
    Правильно обрабатывает порядок байт.
*/
template <typename T> inline T read(const char *src)
{
    return qFromBigEndian<T>(reinterpret_cast<uchar*>(const_cast<char*>(src)) );
}



#endif /* TRIECOMPILEDNODE_H_ */
