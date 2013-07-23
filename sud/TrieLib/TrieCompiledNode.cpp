/*
 * TrieCompiledNode.cpp
 *
 *  Created on: 11.09.2009
 *      Author: Silver
 */

#include "TrieCompiledNode.h"

//#define DEBUG_OUTPUT


/*!
    Создаёт новый узел
 */
TrieCompiledNode::TrieCompiledNode()
        : p(0), buffer(0), chainIndex(0)
{
}

/*!
    Создаёт узел на словаре \a buffer по смещению \a offset
 */
TrieCompiledNode::TrieCompiledNode(const char *buffer, quint32 offset, quint8 chainIndex)
{
    this->buffer = buffer;
    setOffset(offset, chainIndex);
}



TrieCompiledNode::~TrieCompiledNode() {
}


/*!
    Загружает узел состоянием по смещению \a offset.

    Для узлов типа Chain необходимо указывать параметр \a chainIndex.
    \param offset     Смещение узла относительно начала буфера.
    \param chainIndex Указатель на символ внутри цепочки.
 */
bool TrieCompiledNode::setOffset(quint32 offset, quint8 chainIndex)
{
    p = buffer + offset;
    this->chainIndex = chainIndex;
    return true;
}



/*!
    Значение узла (для OneChain) или цепочки (для Chain).
*/
quint8 TrieCompiledNode::value() const
{

    if ((type() == Chain) && chainIndex)                   // Если находимся в цепи, обрабатываем цепь
        return childIndex(chainIndex - 1);


    TrieCompiledNode t(buffer, parentOffset());

    return t.childIndex(parentIndex());
}


/*!
    Заголовок узла.

    Заголовок состоит из типа и флагов.
*/
quint8 TrieCompiledNode::header() const
{
    return *reinterpret_cast<const quint8*>(p);
}


/*!
    Тип узла.
*/
TrieCompiledNode::NodeType TrieCompiledNode::type() const
{
    return NodeType(*(reinterpret_cast<const char *>(p)) & 0x07);
}


/*!
    Смещение узла.
*/
quint32 TrieCompiledNode::offset() const
{
    return quint32(p - buffer);
}


/*!
    Смещение родительского узла
*/
quint32 TrieCompiledNode::parentOffset() const
{
    return offset() - read<quint32>(p + 1);
}


/*!
    Индекс текущего узла в списке дочерей родителя
*/
quint8 TrieCompiledNode::parentIndex() const
{
    return *reinterpret_cast<const quint8*>(p + 1 + 4);
}

/*!
    Количество дочерних узлов
*/
quint8 TrieCompiledNode::childCount() const
{
    return type() == OneChar? *reinterpret_cast<const quint8*>(p + 1 + 4 + 1) : 1;
}

/*!
    Длина цепочки (только для узлов типа Chain)
*/
quint8 TrieCompiledNode::chainLength() const
{
    return *reinterpret_cast<const quint8*>(p + 1 + 4 + 1);     // Пропускаем header и parent
}


/*!
    Возвращает смещение дочернего узла с индексом \a index.

    Работает только для узлов типа OneChar
 */
quint32 TrieCompiledNode::childOffset(int index) const
{
    Q_ASSERT( type() == OneChar );

    int o = read<quint32>(p + 4 + 1 + 2 + this->childCount() + index*sizeof(quint32));

    return offset() + o;
}


/*!
    Возвращает значение дочернего узла.

    \param index Индекс возвращаемого узла.
 */
quint8 TrieCompiledNode::childIndex(int index) const
{
    switch (type()) {
    case OneChar:
    {
        Q_ASSERT( index >= 0 && index < childCount());
        return *reinterpret_cast<const quint8*>(p + 4 + 2 + 1 + index);
    }

    case Chain:
    {
        Q_ASSERT ( index >= 0 && index < chainLength() );
        return *reinterpret_cast<const quint8*>(p + 4 + 2 + 1 + index);
    }

    default:
        Q_ASSERT_X(false, "childIndex()", "Cannot be called for this node type!");
        return 0;
    }

}


/*!
    Пропускает текущий узел типа Chain и возвращает смещение следующего узла.
 */
quint32 TrieCompiledNode::skipChainNode()
{
    Q_ASSERT( type() == Chain );

    const char *t = p + 4 + 1 + 2 + chainLength();
    quint8 dataCount;
    quint8 dataLen;

    if (header() & HasData) {				// Собственные данные
        dataLen = *reinterpret_cast<const quint8*>(t);
        t += 1 + dataLen;
    }


    dataCount = *reinterpret_cast<const quint8*>(t);
    t += 1 + dataCount;                                 // Индексы узлов, у которых есть данные
    if (header() & ChainSameData)
        dataCount = 1;

    while (dataCount--) {
        dataLen = *reinterpret_cast<const quint8*>(t);
        t += 1 + dataLen;
    }

    return t - buffer;
}


/*!
    Пытается найти дочерний узел c и перейти к нему.

    Возвращает true в случае успеха, false - если узла со значением c нет списке дочерних узлов.
    Не изменяет состояние узла в случае неуспеха.
 */
bool TrieCompiledNode::iterateToChild(char c)
{
#ifdef DEBUG_OUTPUT
    qDebug() << "iterateToChild(" << c << "nodeType: " << type() << "offset: " << offset();
#endif
    quint8 value = c;

    switch (type()) {

    case OneChar:
    {

        const quint8 *t = reinterpret_cast<const quint8*>(p + 4 + 1 + 2);
        quint8 b;
        for (quint8 i = 0; i < childCount(); i++)
        {
            b = *(t++);
            if (b == value) {
                setOffset(childOffset(i));
                nodeValue = value;
                return true;
            }
        }
        return false;
    }

    case Chain:
    {
        if (chainIndex < chainLength())
        {
            quint8 t = *reinterpret_cast<const quint8*>(p + 4 + 1 + 2 + chainIndex);
            if ( t == value) {
                ++chainIndex;
                nodeValue = value;
                if (!(header() & ChainTerminated) && (chainIndex >= chainLength()))
                    setOffset(skipChainNode());
                return true;
            }
        }
        return false;
    }


    case Terminator:
    default:
        return false;
    }

}



/*!
    Переходит к дочернему узлу с индексом \a index.

    Если \a index выходит за допустимые границы, возвращает false и оставляет узел неизменным.
 */
bool TrieCompiledNode::iterateToChildIndex(int index)
{
    if (index >= childCount() || index < 0)
        return false;

    quint8 value;

    switch (type())
    {
    case OneChar:
        value = childIndex(index);
        nodeValue = value;

        setOffset(childOffset(index));
        break;

    case Chain:
        if ((chainIndex >= chainLength()) && (header() & ChainTerminated))
            return false;
        value = childIndex(chainIndex);
        nodeValue = value;
        chainIndex++;
        if ((chainIndex >= chainLength()) && !(header() & ChainTerminated))
            setOffset(skipChainNode());
        break;

    default:
        return false;
    }

    return true;
}





/*!
    Возвращает список всех ближайших дочерних узлов, значения которых содержатся stopSymbols

    В основном этот метод используется для нахождения ближайших слов.
    \param stopSymbols Список искомых символов
    \see completeWord()
 */
QList<TrieCompiledNode*> TrieCompiledNode::descents(const QList<quint8> &stopSymbols)
{
    QTime t;
    t.start();

    QList<TrieCompiledNode*> res;
    QStack <int> levels;
    QStack <quint32> nodeOfssets;
    QStack <quint32> nodeChainIndex;
    TrieCompiledNode n(buffer, offset(), chainIndex);
    levels.push(-1);
    nodeOfssets.push(offset());
    nodeChainIndex.push(chainIndex);

    int childIndex;

    //! Тип выполняемого конечным автоматом действия
    enum Action {
        Next,           /*!< Переход к следующему символу */
        LevelUp,        /*!< Вернутся на уровень вверх (назад) */
        Finish          /*!< Выход из цикла */
    } action = Next;


    quint64 iterCounter = 0;
    while (true)
    {
        ++iterCounter;
        switch (action)
        {

        case Next:                                                  // ------------------------ Next
#ifdef DEBUG_OUTPUT
            qDebug() << "Next" << n.fullPath(); // << "Node: " << child.value() << levels;
#endif
            if (levels.isEmpty())
            {
                action = Finish;
                break;
            }

            childIndex = levels.pop();
            n.setOffset(nodeOfssets.top(), nodeChainIndex.top());
            if (!n.iterateToChildIndex(++childIndex))
            {
                nodeOfssets.pop();
                nodeChainIndex.pop();
                action = LevelUp;
                continue;
            }

//            qDebug() << "current path: " << n.fullPath();
            levels.push(childIndex);

//            path += child.value();

//            if (n.fullPath() == "natura ")
//            {
//                bool StopHere = true;
//                qDebug() << "FFFFF: ";
//                qDebug() << n.fullPath();
//            }

            if (stopSymbols.contains(n.value()))    				// Достигли конца слова или строки
            {
#ifdef DEBUG_OUTPUT
                qDebug() << "RESULT:" << n.fullPath();
#endif
                res.append(new TrieCompiledNode(buffer, n.offset(), n.getChainIndex()));
//                res.append(new TrieCompiledNode(buffer, n.parentOffset(), n.parentIndex()));
                action = LevelUp;
                continue;
            }

            levels.push(-1);            // Подготовка следующего уровня
            nodeOfssets.push(n.offset());
            nodeChainIndex.push(n.chainIndex);
            break;

        case LevelUp:                                                   // ------------------------ LevelUp
#ifdef DEBUG_OUTPUT
            qDebug() << "Level Up";
#endif
//            path.remove(path.length() - 1, 1);
            action = Next;
            break;

        case Finish:                                                    // ------------------------ Finish
        default:
#ifdef DEBUG_OUTPUT
            qDebug() << "Finish";
#endif
//            qDebug() << "Descents: " << iterCounter << "iterations...";
//            qDebug() << "Descents: " << res.count() << "completion results... ";
//            qDebug() << "Descents: " << t.elapsed() << "ms...";
            return res;
        }

    }

    Q_ASSERT_X(false, "TrieCompiledNode::descents()", "State machine infinity loop exited");
    return res;

}



/*!
    Возвращает список окончаний строки str до ближайшего слова
 */
QList<TrieCompiledNode *> TrieCompiledNode::completeWord()
{
    return descents(QList<quint8>() << ' ' << '$');
}


/*!
    Возвращает указатель на область пользовательских данных.

    Длина блока возвращается в \a len.
*/
const quint8 *TrieCompiledNode::userDataPtr(int *len)
{
    quint8 t;
    const quint8* ptr;
    *len = 0;

    switch (type()) {

    case OneChar:
    {
        if (header() & HasData)
        {
            ptr = reinterpret_cast<const quint8*>(p + 4 + 1 + 2 + childCount() + childCount() * sizeof(quint32(0)));
            *len = *reinterpret_cast<const quint8*>(ptr);
            return ptr + 1;
        } else
            return 0;
        break;
    }

    case Chain:
    {
        quint8 dataCount;
        quint8 dataLen;
        quint8 dataPos;
        quint8 foundPos;
        bool found = false;

        ptr = reinterpret_cast<const quint8*>(p + 1 + 4 + 1 + 1 + chainLength());

        if ((header() & HasData) ) {														// Пропускаем собственные данные
            dataLen = *reinterpret_cast<const quint8*>(ptr);
            if (chainIndex == 0) {
                // Если запрашивали "собственные" данные цепочки, то вот они
                *len = dataLen;
                return ptr + 1;
            }
            ptr += 1 + dataLen;
        }

        dataCount = *(ptr++);
        for (int i = 0; i < dataCount; i++) {
            dataPos = *(ptr++);
            if (dataPos == (chainIndex - 1)) {
                foundPos = (quint8) i;
                found = true;
            }
        }

        if (!found)
            return 0;

        if (header() & ChainSameData)
            foundPos = 0;

        while (foundPos--) {
            dataLen = *reinterpret_cast<const quint8*>(ptr);
            ptr += 1 + dataLen;
        }

        dataLen = *reinterpret_cast<const quint8*>(ptr);
        ptr += 1;
        *len = dataLen;
        return ptr;
    }


    case Terminator:
        if (header() & HasData)
        {
            ptr = reinterpret_cast<const quint8*>(p + 4 + 1 + 1);
            quint8 dataLen = *reinterpret_cast<const quint8*>(ptr);
            *len = dataLen;
            return ptr + 1;
        } else
            return 0;

    default:
        return 0;
    }
}


/*!
    Возвращает строку пользовательских данных, ассоциированных с узлом.

    Если \a dataRole dataRole == -1 (по умолчанию), возвращает всю строку, как она есть.
    Если \a dataRole dataRole >= 0, возвращает указанную часть данных
 */
QString TrieCompiledNode::userData()
{
    int len;
    const quint8 *ptr = userDataPtr(&len);
    if (!ptr || !len)
        return QString();

    QString res(len, Qt::Uninitialized);
    quint8 t;
    for (int i = 0; i < len; i++)
    {
        t = *(ptr++);
        res[i] = t;
    }
    return res;
}



/*!
    Сравнение двух узлов.
*/
bool TrieCompiledNode::equals(TrieCompiledNode *other) const
{
    return ((this->p == other->p) &&
              (type() != Chain ||
             ((type() == Chain) && (this->chainIndex == other->chainIndex))));
}

/*!
    Возвращает строку, на которую указывает узел.
*/
QString TrieCompiledNode::fullPath() const
{
    QByteArray res;
    TrieCompiledNode n(buffer, offset());

    if (type() == Chain)                        // Если находимся в цепи, обрабатываем цепь
    {
        for (int i = chainIndex; i--; )
            res.prepend( childIndex(i) );
    }

    do
    {
        quint32 nOffset = n.offset();
        quint32 pOffset = n.parentOffset();
        quint8 i = n.parentIndex();

        Q_ASSERT_X ( !((nOffset - pOffset) && !nOffset), "fullPath()", "zero reference to parent node" );

        n.setOffset(pOffset);

        switch (n.type()) {
        case OneChar:
            res.prepend(n.childIndex(i));
            break;

        case Chain:
            for (int i = n.chainLength(); i--; )
                res.prepend( n.childIndex(i) );
            break;

        default:
            res.prepend("?");
        }

    } while (n.offset());

    return QTextCodec::codecForName("Windows-1251")->toUnicode(res);
}




/*!
    Возвращает родительский узел.
*/
TrieCompiledNode TrieCompiledNode::parent() const
{
    if (!offset())
        return TrieCompiledNode(buffer, 0, 0);

    if ((type() == Chain) && chainIndex)                   // Если находимся в цепи, обрабатываем цепь
        return TrieCompiledNode(buffer, offset(), chainIndex - 1);
    else
        return TrieCompiledNode(buffer, parentOffset(), parentIndex());
}
