
/*
 * TrieCompiled.cpp
 *
 *  Created on: 11.09.2009
 *      Author: Silver
 */

#include <QTextCodec>

#include "TrieCompiled.h"


/*!
    Загружает дерево из буфера \a buffer.

    \param buffer   Указатель на скомпилированный словарь.

*/
TrieCompiled::TrieCompiled(const char *buffer)
{
    setBuffer(buffer);
}


/*!
    Загружает дерево из файла \a filename
 */
TrieCompiled::TrieCompiled(const QString &filename)
        : m_buffer(0)
{
    QFile f(filename);
    if (!f.open(QFile::ReadOnly))
        return;

    tempBuffer = f.readAll();
    setBuffer(tempBuffer.data());
    f.close();
}


TrieCompiled::~TrieCompiled() {
}


/*!
    Загружает словарь из буфера \a buffer
*/
void TrieCompiled::setBuffer(const char *buffer)
{
    if (buffer[0] != 'Y' || buffer[1] != 'S' || buffer[2] != '!' || buffer[3] != '\0') {
        qWarning() << "Invalid dictionary signature!";
        m_buffer = 0;
        // TODO: Кидать exception или сигнализировать о провале как-нибудь ещё
        return;
    }
    m_buffer = buffer;
    quint32 dataOffset = read<quint32>(buffer + 4);
    m_dataStart = buffer + dataOffset;
    m_metaData = _readMetaData(buffer + 4 + 4);
}


/**
    Возвращает словарь мета-данных, прочитанных из области памяти, на которую
    указывает ptrMetaData.
*/
TrieCompiled::MetaDataMap TrieCompiled::_readMetaData(const char *ptrMetaData)
{
    MetaDataMap result;
    quint32 len;
    const char *p = ptrMetaData;
    while ( (len = read<quint32>(p)) != 0xffffffff) {
        p += 4;
        QString key = QString::fromUtf8(p, len);
        p += len;
        len = read<quint32>(p);
        p += 4;
        QByteArray value = QByteArray::fromRawData(p, len);
        p += len;
        result[key] = value;
    }
    return result;
}


/*!
    Возвращает указатель на словарь.
*/
const char *TrieCompiled::buffer() const
{
    return m_buffer;
}



/*!
    Ищет образец \a pattern и возвращает список подходящих узлов.
 */
QList<TrieCompiledNode *> TrieCompiled::searchPattern(const QString &pattern)
{
    enum Action { Next,
                  NotFound,
                  Finish
                } action = Next;

    static QTextCodec *codec = QTextCodec::codecForName("Windows-1251");
    QByteArray _pattern = codec->fromUnicode(pattern);
    QList<TrieCompiledNode *> res;
    int i = -1;
    TrieCompiledNode *n = new TrieCompiledNode(m_dataStart, 0);
    char c;
    QStack<State*> stack;
    State *state;
    bool found;


    while (true)
        switch (action) {
        case Next:
            ++i;
            if (i >= _pattern.size()) {					// Достигли конца искомого слова
                res.append(new TrieCompiledNode(m_dataStart, n->offset(), n->getChainIndex()));
//				qDebug() << "Res: " << n.fullPath() << "*";
                action = NotFound;
                break;
            }

            c = _pattern[i];

//			qDebug() << "Next: " << n->fullPath() << c;

            switch (c) {

            case '[':						// Начало множества
                state = new State;
                state->char_set_len = 0;
                for (i++; (i < _pattern.size()) && (_pattern[i] != ']'); i++)
                {
                    state->char_set[state->char_set_len++] = _pattern[i];
                }
//				qDebug() << "Begin set: " << state->char_set;
                state->child_number = -1;
//				state->node = new TrieCompiledNode(n);
                state->nodeOffset = n->offset();
                state->chainIndex = n->getChainIndex();
                state->pos = i;
                state->pattern = State::OneOfSet;
                stack.push(state);
                action = NotFound;
                break;

            case '.':						// Любой символ
                state = new State;
                state->child_number = -1;
//				state->node = n;
                state->nodeOffset = n->offset();
                state->chainIndex = n->getChainIndex();
                state->pos = i;
                state->pattern = State::AnyChar;
                stack.push(state);          // Создаём точку останова
                action = NotFound;
                break;

            default:						// Строгое совпадение
                if (!n->iterateToChild(c))	//		n = n->child(c);
                    action = NotFound;
                break;
            }

            break;



        case NotFound:
            // Возвращаемся к точке останова. Если возвращаться некуда, выходим
//			qDebug() << "Not found" << c;

            if (stack.isEmpty()) {
                action = Finish;
                break;
            }

            state = stack.pop();
//			n = state->node;
            n->setOffset(state->nodeOffset, state->chainIndex);
            found = false;

            if (state->pattern == State::AnyChar) {
                found = n->iterateToChildIndex(++state->child_number);
            }
            else if (state->pattern == State::OneOfSet) {
                int &i = state->child_number;
                while (!found && (++i < state->char_set_len) ) {
                    c = state->char_set[i];
                    if (c != '?') {
                        found = n->iterateToChild(c);			// n = state->node->child(c);
                    } else {
                        found = true; // n = state->node;
                    }
                }
            }

            if (!found) {
                delete state;
                break;					// Точка останова отработала. action = NotFound
            }

//			qDebug() << "Skip to" << n.fullPath();

            stack.push(state);
            i = state->pos;
            action = Next;
            break;

        case Finish:
        default:
            delete n;
            return res;

        }
}


QByteArray TrieCompiled::metaData(const QString &key) const
{
    return m_metaData.value(key);
}


void TrieCompiled::setMetaData(const QString &key, const QByteArray &value)
{
    m_metaData[key] = value;
}


void TrieCompiled::setMetaData(const QString &key, const QString &value)
{
    m_metaData[key] = value.toUtf8();
}

