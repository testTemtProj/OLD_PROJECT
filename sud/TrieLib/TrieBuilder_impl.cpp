#include <QDataStream>
#include <QVector>
#include <QMap>
#include <QSet>
#include "TrieBuilder.h"

class TrieBuilderImpl {
public:
    TrieBuilderImpl()
        : m_root(new BuilderNode(0,0)), m_nodeCount(0)
    {
    }


    BuilderNode *addNode(char_t value, BuilderNode *parent)
    {
        if (!parent)
            return 0;
        // Если значение уже содержится, возвращаем указатель на него
        foreach (BuilderNode *n, parent->m_children) {
            if (n->value() == value)
                return n;
        }

        // Создаём новый узел
        BuilderNode *node = new BuilderNode(value, parent);
        parent->m_children.append(node);
        m_nodeCount++;
        return node;
    }

    BuilderNode *root() const
    {
        return m_root;
    }


    int nodeCount() const
    {
        return m_nodeCount;
    }


    /** Сохраняет словарь в устройство \a out.

        Формат словаря:

            4 байта     'YS!\0'         Сигнатура
            4 байта     quint32         Смещение начала данных
            x байт                      Мета-данные
            ...................         Данные
    */
    void save(QIODevice &out)
    {
        if (!out.isOpen() || !out.isWritable())
            out.open(QIODevice::ReadWrite | QIODevice::Truncate);
        QDataStream data(&out);
        saveHeader(data);
        qint64 offset = data.device()->pos();
        saveNode(data, root(), offset, offset, 0);
    }


    /** Сохраняет заголовок словаря */
    void saveHeader(QDataStream &data)
    {
        // Сигнатура
        data << (quint8) 'Y' << (quint8) 'S' << (quint8) '!' << (quint8) '\0';

        // Место для смещения начала данных
        data << (quint32) 0;

        saveMetaData(data);

        quint32 offset = data.device()->pos();
        data.device()->seek(4);
        data << (quint32) offset;
        data.device()->seek(offset);
    }


    /** Сохраняет метаданные словаря.

        Записи мета-данных храняться друг за другом в таком формате:

        4 байта     длина ключа
        x байт      строка ключа в Utf-8
        4 байта     длина данных, ассоциированных с ключём
        x байт      мета-данные

        После последней записи идут четыре байта терминатора 0xFFFFFFFF.
    */
    void saveMetaData(QDataStream &data)
    {
        foreach (QString key, m_metaData.keys()) {
            writeLongByteArray(data, key.toUtf8());
            writeLongByteArray(data, m_metaData[key]);
        }
        data << (quint32) 0xffffffff;
    }


    /*!
        Сохраняет узел \a n со всеми дочерними узлами в поток \a data.

        Возвращает конечное смещение узла \a n.

        \param data         Поток, в который производится сохранение
        \param n            Узел, который будет сохранён со всеми потомками
        \param offset       Смещение, по которому начнётся запись узла \a n.
        \param parentOffset Смещение родительского узла
        \param parentIndex  Индекс узла \a n среди дочерних узлов \a parent
     */
    quint64 saveNode(QDataStream &data, BuilderNode *n, quint64 offset,
                     quint64 parentOffset, qint8 parentIndex)
    {
        data.device()->seek(offset);

        int count = n->children().count();

        quint8 type;

        if (count == 0)
            type = BuilderNode::Terminator;
        else if (count == 1)
            type = BuilderNode::Chain;
        else
            type = BuilderNode::OneChar;

        bool hasData = !n->data().isEmpty();

        quint8 typeWithFlags = type;
        if (hasData)
            typeWithFlags |= BuilderNode::HasData;

        parentOffset = offset - parentOffset;


        quint64 posOffsets;
        quint64 nextChildOffset;

        switch (type) {

        case BuilderNode::OneChar:															// Узел, имеющий нескольких детей
            data << typeWithFlags;
            data << (quint32) parentOffset;                // [parent]
            data << (quint8) parentIndex;
            data << (quint8) count;
            for (int i = 0; i < count; i++)
                data << (quint8) n->child(i)->value();
            posOffsets = data.device()->pos();
            for (int i = 0; i < count; i++)
                data << (quint32) 0;

            if (hasData) {
                writeByteArray(data, n->data());
            }

            nextChildOffset = data.device()->pos();
            for (int i = 0; i < count; i++) {
                data.device()->seek(posOffsets + i * sizeof(quint32));
                data << (quint32) (nextChildOffset - offset);
                nextChildOffset = saveNode(data, n->child(i), nextChildOffset, offset, i);
            }

            return nextChildOffset;


        case BuilderNode::Chain:																// Цепочка по одному символу
        {
            data << typeWithFlags;
            data << (quint32) parentOffset;                // [parent]
            data << (quint8) parentIndex;

            QVector<char_t> chain;
            QMap<int, QByteArray> mapData;
            QByteArray ownData = n->data();

            while (n->children().count() == 1) {
                n = n->child(0);
                chain.append(n->value());
                if (!n->data().isEmpty()) {
                    mapData[chain.size() - 1] = n->data();
                }
            }

            data << (quint8) chain.size();
            foreach(char_t v, chain)
                data << (quint8) v;

            if (hasData)                            // Собственные данные
                writeByteArray(data, ownData);

            QList<int> keys = mapData.keys();       // Кол-во данных
            data << (quint8) keys.length();         // Индексы символов с данными
            foreach (int key, keys) {
                data << (quint8) key;
            }

            if (!hasSameValues(mapData)) {
                foreach (int key, keys) {
                    writeByteArray(data, mapData[key]);
//                    data << (quint8) mapData[key].length();     // Кол-во данных
//                    saveString(data, mapData[key]);             // Данные узлов
                }
            }
            else {
                typeWithFlags |= BuilderNode::ChainSameData;
                QByteArray nodeData = mapData.values()[0];
                writeByteArray(data, nodeData);
                nextChildOffset = data.device()->pos();
                data.device()->seek(offset);
                data << typeWithFlags;
                data.device()->seek(nextChildOffset);
            }

            if (n->children().count() == 0) {
                nextChildOffset = data.device()->pos();
                typeWithFlags |= BuilderNode::ChainTerminated;
                data.device()->seek(offset);
                data << typeWithFlags;
                return nextChildOffset;
            }

            return saveNode(data, n, data.device()->pos(), offset, chain.size() - 1);
        }

        case BuilderNode::Terminator:
            data << typeWithFlags;
            data << (quint32) parentOffset;                // [parent]
            data << (quint8) parentIndex;
            if (hasData)
                writeByteArray(data, n->data());
            return data.device()->pos();

        default:
            data << type;
            data << (quint32) parentOffset;                // [parent]
            data << (quint8) parentIndex;
            return data.device()->pos();
        }
    }

    /*!
        Сохраняет \a array в поток \a data.

        Длина массива ограничена 255 байтами.
     */
    void writeByteArray(QDataStream &data, const QByteArray &array)
    {
        int length = array.length();
        Q_ASSERT( length < 255 );
        data << (quint8) length;
        data.writeRawData(array.data(), length);
    }

    /*!
        Сохраняет \a array в поток \a data.

        Длина массива ограничена 4 Гб.

        Внимание: массивы, сохранённые этой функцией и writeByteArray никак не
        различаются, необходимо следить за корректным чтением.
     */
    void writeLongByteArray(QDataStream &data, const QByteArray &array)
    {
        quint32 length = array.length();
        data << (quint32) length;
        data.writeRawData(array.data(), length);
    }

    /*!
        Возвращает true, если карта содержит все одинаковые значения.
     */
    bool hasSameValues(const QMap<int, QByteArray> &map)
    {
        if (map.count() < 2)
            return false;
        return QSet<QByteArray>::fromList(map.values()).count() == 1;
    }

    /*!
      Устанаваливает метаданные \a data по ключу \a key
    */
    void setMetaData(const QString &key, const QByteArray &data)
    {
        m_metaData[key] = data;
    }


    /*!
      Устанаваливает метаданные \a data по ключу \a key.
      Строка сохраняется в UTF-8.
    */
    void setMetaData(const QString &key, const QString &data)
    {
        m_metaData[key] = data.toUtf8();
    }

    /*!
      Возвращает метаданные по ключу \a key.
    */
    QByteArray metaData(const QString &key)
    {
        return m_metaData.value(key);
    }



private:
    BuilderNode *m_root;
    int m_nodeCount;
    QMap<QString, QByteArray> m_metaData;
};

