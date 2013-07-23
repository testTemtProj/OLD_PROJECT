/*
 * TrieSpeller.cpp
 *
 *  Created on: 26.08.2009
 *      Author: Silver
 */


#include "TrieSpeller.h"
#include "LingvoTools.h"
#include "FixLayout.h"

//#define	DEBUG_OUTPUT 1

TrieSpeller::TrieSpeller()
        : tree(0)
{
    config.fixLayout = false;
    config.fixSpelling = false;
    config.fixSpellingLight = false;
    config.minSpellingLen = 0;
    config.phoneticSort = false;
}

TrieSpeller::~TrieSpeller() {
}



/*!
    Загружает скомпилированный словарь из файла filename
 */
bool TrieSpeller::loadDictionaryFromFile(const QString &filename)
{
    tree = new TrieCompiled(filename);
    if (!tree->buffer())
        return false;
    loadThemesList();

    tree->setMetaData("_source", QString("file://") + filename);
    return true;
}



/*!
    Загружает словарь из разделяемой памяти
*/
bool TrieSpeller::loadDictionaryFromSharedMemory(const QString &key)
{
    shared.setKey(key);
    if (!shared.attach(QSharedMemory::ReadOnly))
    {
        qDebug() << "Error attaching shared memory:" << shared.errorString();
        return false;
    }
    return loadDictionaryFromRawData((const char *)shared.constData());
}


/*!
    Загружает словарь из области памяти, на которую указывает \a data
*/
bool TrieSpeller::loadDictionaryFromRawData(const char *data)
{
    tree = new TrieCompiled(data);
    if (!tree->buffer())
        return false;
    loadThemesList();
    return true;
}


/*!
 * Загружает соответствия id тематик их развёрнутым названиям.
 */
bool TrieSpeller::loadThemesList()
{
    Q_ASSERT( tree != 0);

    QStringList theme_lines = QString(tree->metaData("_themes")).split('\n');
    foreach (QString line, theme_lines) {
        int pos = line.indexOf(':');
        if (pos < 0)
            continue;
        mapLocalizedThemes[line.left(pos)] = line.mid(pos + 1);
    }
    return true;
}


/*!
    Удаляет из списка nodes повторяющиеся элементы.
 */
void TrieSpeller::removeDuplicateNodes(node_list &nodes, node_list *matches)
{
    if (matches)
        Q_ASSERT(nodes.length() == matches->length());

    typedef QPair<const char *, quint8> PointerChain;

    QSet<PointerChain> pointer_chains;

    for (int i = nodes.size() - 1; i >= 0; i--) {
        TrieCompiledNode *node = nodes[i];
        quint8 chainIndex;
        if (node->type() == TrieCompiledNode::Chain)
            chainIndex = node->getChainIndex();
        else
            chainIndex = 0;

        PointerChain pointer_chain =
                qMakePair(node->getHeaderPointer(), chainIndex);

        if (pointer_chains.contains(pointer_chain)) {
            nodes.removeAt(i);
            if (matches)
                matches->removeAt(i);
        } else
            pointer_chains.insert(pointer_chain);
    }
}



/*!
    Пытается исправить раскладку (каждого слова в отдельности).

    Кеширует результат последнего запроса.
 */
bool TrieSpeller::fixLayout(QString &str)
{
    static QString cache_str;
    static QString cache_fixed;
    static bool cache_result;

    if (str == cache_str) {
        str = cache_fixed;
        return cache_result;
    }

    cache_str = str;

    QStringList words = str.split(' ', QString::SkipEmptyParts);
    QString current;
    QString t;
    QString word;
    FixLayout fix;
    int i = 0;

    enum Action {
        FeedWord,
        TryOriginal,
        TrySwitched,
        FinishedOk,
        NotFound
    } action = FeedWord;

    while (true) {
        switch (action) {
        case FeedWord:
            action = TryOriginal;

            if (i >= words.count())
                action = FinishedOk;
            else if (i == (words.count() - 1) )
                word = words[i];
            else if (i == 0)
                word = words[i] + " ";
            else
                word = words[i] + " ";

//			qDebug() << "";
//			qDebug() << "FeedWord: " << word;
            ++i;
            break;

        case TryOriginal:
            t = current + cleanString(word);

//			qDebug() << "TryOriginal:" << t;
//			qDebug() << tree->searchPattern(t).count() << "results";

            if (tree->searchPattern(escapeSpaces(t)).count()) {
                current = t;
                action = FeedWord;
            } else
                action = TrySwitched;

            break;

        case TrySwitched:
            t = current + cleanString(fix.convertLayout(word));

//			qDebug() << "TrySwitched" << current + fix.convertLayout(word);
//			qDebug() << tree->searchPattern(t).count() << "results";

            if (tree->searchPattern(escapeSpaces(t)).count()) {
                current = t;
                action = FeedWord;
            } else
                action = NotFound;
            break;

        case FinishedOk:
            str = t;
            cache_fixed = str;
            cache_result = true;
            return true;

        case NotFound:
        default:
            cache_fixed = str;
            cache_result = false;
            return false;
        }
    }
}


/*!
    Извлекает из строки данных узла информацию о весе тематик.
*/
int TrieSpeller::CountersRateData(TrieCompiledNode *n, const QString &theme)
{
    QString str = n->userData();

    return ParseRateData(str, theme);
}


/*!
    Извлекает из данных узла информацию о количестве следующих за узлом записей
    с разбивкой по тематикам.
*/
int TrieSpeller::CountersCountData(TrieCompiledNode *n, const QString &theme)
{
    QString str = n->userData();

    Q_ASSERT_X(!str.isEmpty(), "CountersCountData",
               "Attempt to parse empty data string!");

    return ParseCountersData(str, theme);
}


/** Ищет в строке данных \a data рейтинг тематик */
int TrieSpeller::ParseCountersData(const QString &data, const QString &theme) const
{
    enum {
        IN_THEME,
        IN_COUNT,
        IN_RATE,
        ADVANCE_TO_NEXT_THEME,
        NOT_FOUND
    } state = IN_THEME;

    int pos = -1;
    int posStart = 0;
    int len = 0;
    int datalen = data.length();

    forever {
        pos++;

        switch (state) {
        case IN_THEME:
            if (pos == datalen || data[pos] == ':') {
                // Дошли до конца темы
                QString t = data.mid(posStart, len);
                if ( t != theme) {
                    // Не та тема, переходим к следующей
                    state = ADVANCE_TO_NEXT_THEME;
                    continue;
                } else {
                    // Нужная тема, переходим к получению счётчика
                    state = IN_COUNT;
                    posStart = pos + 1;
                    len = 0;
                    continue;
                }
            } else {
                // Ещё не дошли до конца темы
                len++;
            }
            break;

        case IN_COUNT:
            if (pos == datalen || data[pos] == ':') {
                // Дошли до конца счётчика
                return data.mid(posStart, len).toInt();
            } else {
                // Ещё не дошли до конца счётчика
                len++;
            }
            break;

        case ADVANCE_TO_NEXT_THEME:
            if (pos == datalen) {
                state = NOT_FOUND;
                continue;
            }

            if (data[pos] == ';') {
                posStart = pos + 1;
                len = 0;
                state = IN_THEME;
            }
            break;

        case NOT_FOUND:
            return 0;

        case IN_RATE:
        default:
            Q_ASSERT_X(false, "ParseCountersData()", "Should not be there!");
            return 0;
        }
    }

    return 0;
}


/** Ищет в строке данных \a data рейтинг тематик */
int TrieSpeller::ParseRateData(const QString &data, const QString &theme) const
{
    enum {
        IN_THEME,
        IN_COUNT,
        IN_RATE,
        ADVANCE_TO_NEXT_THEME,
        ADVANCE_TO_NEXT_COUNTER,
        NOT_FOUND
    } state = IN_THEME;

    int pos = -1;
    int posStart = 0;
    int len = 0;
    int datalen = data.length();

    forever {
        pos++;

        switch (state) {
        case IN_THEME:
            if (pos == datalen || data[pos] == ':') {
                // Дошли до конца темы
                QString t = data.mid(posStart, len);
                if ( t != theme) {
                    // Не та тема, переходим к следующей
                    state = ADVANCE_TO_NEXT_THEME;
                    continue;
                } else {
                    // Нужная тема, переходим к получению счётчика
                    state = ADVANCE_TO_NEXT_COUNTER;
                    posStart = pos + 1;
                    len = 0;
                    continue;
                }
            } else {
                // Ещё не дошли до конца темы
                len++;
            }
            break;

        case IN_COUNT:
            if (pos >= datalen || data[pos] == ':') {
                // Дошли до конца счётчика
                return data.mid(posStart, len).toInt();
            } else {
                // Ещё не дошли до конца счётчика
                len++;
            }
            break;

        case ADVANCE_TO_NEXT_THEME:
            if (pos >= datalen) {
                state = NOT_FOUND;
                continue;
            }

            if (data[pos] == ';') {
                posStart = pos + 1;
                len = 0;
                state = IN_THEME;
            }
            break;

        case ADVANCE_TO_NEXT_COUNTER:
            if (pos >= datalen) {
                state = NOT_FOUND;
                continue;
            }

            if (data[pos] == ';' || data[pos] == ':') {
                posStart = pos + 1;
                len = 0;
                state = IN_COUNT;
            }
            break;

        case NOT_FOUND:
            return 0;

        case IN_RATE:
        default:
            Q_ASSERT_X(false, "ParseCountersData()", "Should not be there!");
            return 0;
        }
    }

    return 0;
}



/*!
    Преобразует строку string вида "key:value;key:value" в карту
 */
QMap <QString, int> TrieSpeller::stringToMap(const QString &string)
{
    static int i = 0;
    QMap<QString, int> res;

    QStringList pairs = string.split(";", QString::SkipEmptyParts);
    foreach (QString pair, pairs) {
        int i = pair.indexOf(':');
        res[pair.left(i)] += pair.right(pair.length() - i - 1).toInt();
    }

    qDebug() << ++i;

    return res;
}



/*!
    Преобразует карту в строку вида "key:value;key:value"
 */
QString TrieSpeller::mapToString(QMap <QString, int> map)
{
    QString res;

    QStringList keys = map.keys();
    foreach (QString key, keys)
    res.append(key + ":" + QString::number(map[key]) + ";");
    res.chop(1);

    return res;
}






/*!
    Возвращает паттерн поиска строки str с учётом "простых" опечаток:

    1. "а" и "о" взаимозаменяемы ("малако")
    2. "с" и "з" взаимозаменямы ("зделать", "бес платы")
    4. "е" и "и" взаимозаменяемы
    3. Удвоенные "с", "н", "т" считаются необязательными
    4. Пробел и неразрывный пробел -- один и тот же символ
 */
QString TrieSpeller::simpleMisspellsPattern(const QString &str)
{
    QString res;
    static QChar ru_A = QChar(0x0430);
    static QChar ru_O = QChar(0x043E);
    static QChar ru_S = QChar(0x0441);
    static QChar ru_Z = QChar(0x0437);
    static QChar ru_E = QChar(0x0435);
    static QChar ru_I = QChar(0x0438);
    static QChar ru_N = QChar(0x043d);
    static QChar ru_T = QChar(0x0442);


    for (int i = 0; i < str.length(); i++) {
        QChar c = str[i];

        if ( (c == ru_A) || (c == ru_O) )
            res += '[' + ru_A + ru_O + ']';
        else if ( (c == ru_S) ) {
            res += "[сз][с?]";
            while (i+1 < str.length() && str[i+1] == c) ++i;
        }
        else if ( (c == ru_Z) )
            res += "[сз]";
        else if ( (c == ru_E) || (c == ru_I) )
            res += "[еи]";
        else if ( (c == ru_N) || (c == ru_T)) {
            res += c;
            res += "[";
            res += c;
            res += "?]";
            while (i+1 < str.length() && str[i+1] == c) ++i;
        }
        else if ( (c == ' ') || (c == '_'))
            res += "[ _]";
        else
            res += c;
    }
    return res;
}


bool _allowedChar(QChar c)
{
    return c.isLetterOrNumber()
            || (c == ' ') || (c == '(') || (c == ')')  || (c == '-')
            || (c == ',');
}


/*!
    Очищает строку от знаков пунктуации
 */
QString TrieSpeller::cleanString(const QString &str)
{
    QString result(str.size() * 1.5, Qt::Uninitialized);
    int len = str.length();
    int i = 0, j = 0;

    // Пропускаем пробелы в начале строки
    while (i < len && (str[i] == ' ' ||  !_allowedChar(str[i])))
        ++i;

    // Чистим фразу
    bool previous_space = false;
    for (; i < len; ++i) {
        if (str[i] == ' ') {
            if (previous_space)
                continue;
            else
                previous_space = true;
        } else
            previous_space = false;

        if (_allowedChar(str[i]))
            result[j++] = str[i];
    }

    result.truncate(j);

    return result;

    // TODO: Заменять недопустимые символы на пробел, а затем заменять
    // несколько подряд идущих пробелов на один
}


/** Считаем обычный и неразрывный пробел одним и тем же символом. */
QString TrieSpeller::escapeSpaces(const QString &str)
{
    QString result(str);
    result.replace(" ", "[ _]");
    return result;
}


/** Поиск запроса \a query с учётом возможных опечаток.

    Возвращает true, если для получения подсказок пришлось применять
    исправление орфографии.
 */
bool TrieSpeller::SearchMisspeled(const QString &query, node_list &nodes)
{
    // Получаем подсказки к оригинальному слову...
    QString cleanedQuery = cleanString(query);
    nodes = tree->searchPattern(escapeSpaces(cleanedQuery));

    if (!nodes.isEmpty())
        return false;

    // ...если их нет, начинаем пробовать варианты опечаток и раскладок.
    QString fixedQuery(query);
    if (fixLayout(fixedQuery))
        nodes += tree->searchPattern(escapeSpaces(fixedQuery));
    fixedQuery = cleanString(fixedQuery);
    if (config.fixSpelling) {
        QStringList combinations = LingvoTools::wordCombinations(fixedQuery);
        foreach(QString c, combinations)
            nodes += tree->searchPattern(simpleMisspellsPattern(c));
    } else if (config.fixSpellingLight) {
        nodes += tree->searchPattern(simpleMisspellsPattern(fixedQuery));
    }

    removeDuplicateNodes(nodes);

    // Если запрос ничего не дал даже с применением опечаток, считаем что
    // исправление орфографии применять не пришлось
    if (!nodes.isEmpty())
        return true;
    else
        return false;
}


/** Дополнения до ближайшего слова каждого узла из \a nodes.

    \param suggestedNodes будет содержать список всех дополнений

    \param matches будет содержать список matched узлов, т.е. узлов, которыми
                   заканчивается уже "набранная" часть и начинаются подсказки.
                   Длина этого списка такая же, как и у \a suggestedNodes.
                   Каждой подсказке соответствует match узел, т.е. для
                   подсказки suggestedNodes[i] набранная часть будет
                   matches[i].

  */
void TrieSpeller::CompleteWords(const node_list &nodes,
                                node_list &suggestedNodes,
                                node_list &matches)
{
    foreach (TrieCompiledNode *node, nodes) {
        node_list completions = node->completeWord();
        suggestedNodes << completions;

        for (int i = 0; i < completions.size(); i++)
            matches.append(node);
    }
}


/** Все подсказки по запросу \query без каких-либо группировок по тематикам.

    \param is_misspelled будет содержать true, если для получения
                         подсказок потребовалось исправлять орфографию.
    \param result_suggestions будет содержать список подсказок.
    \param matches список match узлов, по одному на каждую подсказку.
                   Индексы элементов соответствуют \a result_suggestions
 */
void TrieSpeller::SuggestAll(const QString &query,
                             node_list &result_suggestions,
                             bool &is_misspelled,
                             node_list &matches)
{
    if (!tree || !tree->buffer()) {
        qWarning() << "Dictionary is not ready!";
        return;
    }

    node_list nodes;
    is_misspelled = SearchMisspeled(query, nodes);
    CompleteWords(nodes, result_suggestions, matches);
}


/** Группирует узлы \a nodes по тематикам.

    \param top      По каждой теме останется не более top результатов
    \param phoneticSort Сортировать по фонетической близости. Улучшает
                    результаты для запросов с опечатками, но может занимать
                    значительное время.
 */
TrieSpellerResults TrieSpeller::GroupNodesByThemes(const node_list &nodes,
                                                   int top,
                                                   const QString &word,
                                                   bool phoneticSort,
                                                   const node_list &matches)
{
    TrieSpellerResults results(mapLocalizedThemes, top, word, phoneticSort);

    int len = nodes.length();
    for (int i = 0; i < len; i++) {
        TrieCompiledNode *n = nodes[i];
        TrieCompiledNode *m = matches[i];
        results.add(n, m);
    }
    return results;
}


/** В случае недобора до \a top подсказок, начинаем разворачивать подсказки до
    следующих слов.
  */
void TrieSpeller::ExpandSuggestions(TrieSpellerResults &results, int top)
{
    QStringList themes = results.themesOrdered();       // TODO: Обязательно ли нужны Ordered?

    bool expandAll = true;
    expandAll = expandAll && themes.count() <= 2;

    foreach (QString theme, themes) {
        ExpandResultsOneTheme(results, top, theme, expandAll);
    }
}


/** Расширяет список предложений \a results по тематике \a theme до \a limit
    результатов. Возвращает расширенные результаты.

    Расширенные подсказки добавляются в конец.

    Если \a expandAll равен true, то будут
 */
void TrieSpeller::ExpandResultsOneTheme(TrieSpellerResults &results, int limit,
                                         const QString &theme, bool expandAll)
{
    TrieSpellerResults::list_results r = results.results(theme);
    int needMore = limit - r.count();
    if (needMore <= 0)
        return;
    TrieSpellerResults extendedResults( mapLocalizedThemes, needMore,
                                        results.query(),
                                        /*phoneticSort =*/ false);

    TrieSpellerResults::list_results mainResults = r;
    // Результаты, помеченные на удаление
    // (родительский узел на удаление => расширенные_узлы)
    QMultiMap<TrieCompiledNode*, TrieCompiledNode*> mainResutsForDeletion;

    foreach (TrieSpellerResults::Result mainResult, mainResults)
    {
        // Берём основной результат и продолжаем его до следующего слова
        node_list extendedNodes = mainResult.node->completeWord();
        int countSumm = 0;
        foreach (TrieCompiledNode *n, extendedNodes)
        {
            int count = CountersCountData(n, theme);
            if (count) {
                int rate = CountersRateData(n, theme);
                TrieCompiledNode *match = mainResult.match;
                extendedResults.add(theme, n, rate, match);
                mainResutsForDeletion.insertMulti(mainResult.node, n);
                countSumm += count;
                /****************** version 1.0: Зачем тут это было?
                if (count > 1)
                    expandAll = false;
                *****************************************************/
            }
        }

//        // Если полностью развернули узел, убираем его
//        int node_count_data = CountersCountData(mainResult.node, theme);
//        node_count_data -= countSumm;
//        if (node_count_data <= 0) {
////				qDebug() << "Parent note fully expanded, removing it";
////                                results.remove(theme, mainResult.node);
//        }
//        else {
//            ;
//        /****************** version 1.0: Зачем тут это было?
//            expandAll = false;
//        *********************************************/
//        }
    }

    // Убираем полностью развёрнутые узлы (у которых все дочерние результаты
    // попали в список)
    foreach (TrieSpellerResults::Result mainResult, mainResults)
    {
        TrieCompiledNode *parent = mainResult.node;

        // Если подсказка не разворачивалась, то и удалять её не нужно
        if (!mainResutsForDeletion.contains(parent))
            continue;

        bool remove = true;
        foreach (TrieCompiledNode *child, mainResutsForDeletion.values(parent)) {
            if (!extendedResults.contains(theme, child)) {
                remove = false;
                break;
            }
        }
        if (remove)
            results.remove(theme, parent );
    }


    results.unite(&extendedResults);

    // Разворачиваем подсказки, по которым остался
    //   единственный вариант продолжения
    if (expandAll)
        ExpandSingleSuggestions(results, theme);

}


/** Разворачивает подсказки, по которым остался лишь один вариант продолжения */
void TrieSpeller::ExpandSingleSuggestions(TrieSpellerResults &results,
                                          const QString &theme)
{
    TrieSpellerResults::list_results list = results.results(theme);
    for (int i = 0; i < list.count(); i++) {
        TrieCompiledNode *node = list[i].node;
        if (node->value() == '$')
            continue;
        int count = CountersCountData(node, theme);
        if (count != 1)
            continue;
        node_list expanded = node->descents();
        for (int j = 0; j < expanded.size(); j++) {
            TrieCompiledNode *n = expanded[j];
            if (CountersCountData(n, theme)) {
                results.remove(theme, node);
                results.add(theme, n, 0, list[i].match);
                break;
            }
        }
    }
}


/*!
    Предлагает \a top вариантов окончания запроса \a word.

    \param word     Строка запроса.
    \param fix      Если true, то пытается исправить опечатку
                    (при условии, что по оригинальному запросу ничего не найдено).
    \param top      Кол-во возвращаемых результатов.
 */
TrieSpellerResults TrieSpeller::suggest(const QString &word, bool , int top)
{
    QTime t;
    t.start();

    node_list suggestedNodes;
    node_list matches;
    bool is_misspelled;
    SuggestAll(word, suggestedNodes, is_misspelled, matches);

    removeDuplicateNodes(suggestedNodes, &matches);

    bool phoneticSort = is_misspelled && config.phoneticSort;
    TrieSpellerResults results =
            GroupNodesByThemes(suggestedNodes, top, cleanString(word),
                               phoneticSort, matches);

    ExpandSuggestions(results, top);
    return results;

}






TrieSpellerResults::TrieSpellerResults(
    const QMap<QString, QString> themeTitleById, int top, const QString &query,
    bool phoneticSort)
    : m_themeTitleById(themeTitleById),
      m_top(top),
      m_query(query),
      m_phoneticSort(phoneticSort)
{
}


/*!
    Добавляет результат (подсказку).

    Если количество результатов по теме \a theme больше \a top, то вытеснит
    результат с низким рейтингом.

    В первую очередь результаты сортируются по фонетической близости (вариант
    редакционного расстояния). Во вторую, по рейтингу \a rate.
 */
void TrieSpellerResults::add(const QString &theme, TrieCompiledNode *node,
                             int rate, TrieCompiledNode *match)
{
    // Изменяем rate с учётом фонетической близости
    if (m_phoneticSort) {
        QString suggest = node->fullPath();
        suggest.truncate(m_query.length());

        int distance = LingvoTools::distancePhonetic(m_query, suggest);
        rate = 30000 + rate * 0.005 - distance * 1000;
    }

    // Вставляем элемент
    list_results &list = m_data[theme];
    if (list.count() < m_top)
        insertSorted(list, node, rate, match);
    else {
        int min = list.last().rate;
        if (rate > min) {
            insertSorted(list, node, rate, match);
            list.removeLast();
        }
    }
}


/*!
    Добавляет узел \a node по всем его тематикам в результаты.

    См. TrieSpellerResults::add(const QString &theme, TrieCompiledNode *node, int rate)
*/
void TrieSpellerResults::add(TrieCompiledNode *node, TrieCompiledNode *match)
{
    enum {
        IN_THEME,
        IN_COUNT,
        IN_RATE,
        ADVANCE_TO_NEXT_THEME,
        ADVANCE_TO_NEXT_COUNTER,
        NOT_FOUND
    } state = IN_THEME;

    int datalen;
    const char *data = reinterpret_cast<const char *>(node->userDataPtr(&datalen));
    int pos = -1;
    int posStart = 0;
    int len = 0;
    QByteArray theme;

    forever {
        pos++;

        switch (state) {
        case IN_THEME:
            if (pos == datalen || data[pos] == ':') {
                // Дошли до конца темы
                theme = QByteArray::fromRawData(data + posStart, len);
                // переходим к получению счётчика
                state = ADVANCE_TO_NEXT_COUNTER;
                posStart = pos + 1;
                len = 0;
                continue;
            } else {
                // Ещё не дошли до конца темы
                len++;
            }
            break;

        case IN_COUNT:
            if (pos >= datalen || data[pos] == ':' || data[pos] == ';') {
                // Дошли до конца счётчика
                int value = QByteArray::fromRawData(data + posStart, len).toInt();
                add(theme, node, value, match);
                state = ADVANCE_TO_NEXT_THEME;
                continue;
            } else {
                // Ещё не дошли до конца счётчика
                len++;
            }
            break;

        case ADVANCE_TO_NEXT_THEME:
            if (pos >= datalen) {
                state = NOT_FOUND;
                continue;
            }

            if (data[pos] == ';') {
                posStart = pos + 1;
                len = 0;
                state = IN_THEME;
            }
            break;

        case ADVANCE_TO_NEXT_COUNTER:
            if (pos >= datalen) {
                state = NOT_FOUND;
                continue;
            }

            if (data[pos] == ':') {
                posStart = pos + 1;
                len = 0;
                state = IN_COUNT;
            }
            break;

        case NOT_FOUND:
            return;

        case IN_RATE:
        default:
            Q_ASSERT_X(false, "ParseCountersData()", "Should not be there!");
            return;
        }
    }

    return;
}



/*!
    Удаляет узел \a node из результатов.
 */
void TrieSpellerResults::remove(const QString &theme, TrieCompiledNode *node)
{
    list_results &list = m_data[theme];
    for (int i = 0; i < list.count(); i++) {
        TrieCompiledNode *listNode = list[i].node;
        if (listNode == node) {
            list.removeAt(i);
            return;
        }
    }
}



/*!
    Вставляет результат в упорядоченный по убыванию список \a list.
 */
void TrieSpellerResults::insertSorted(list_results &list, TrieCompiledNode *n,
                                      int rate, TrieCompiledNode *match)
{
    // TODO: можно заменить на бинарный поиск
    for (int i = 0; i < list.count(); i++)
        if (list[i].rate < rate) {
            list.insert(i, Result(n, rate, match));
            return;
        }
    list.append(Result(n, rate, match));
}




/*!
    Возвращает список тем, задействованных в результатах
 */
QStringList TrieSpellerResults::themes() const
{
    return m_data.keys();
}


/*!
    Возвращает список тем, отсортированных по суммарному рейтингу (в порядке убывания)
 */
QStringList TrieSpellerResults::themesOrdered() const
{
    QMultiMap<int, QString> rates;

    QStringList themes = m_data.keys();
    foreach (QString theme, themes) {
        list_results list = m_data[theme];
        int s = 0;
        for (int i = 0; i < list.count(); i++)
            s += list[i].rate;
        rates.insert(s, theme);
    }

    QStringList values = rates.values();
    QStringList res;

    for (int i = values.count() - 1; i >= 0; i--)
        res << values[i];

    return res;
}


/*! Возвращает полное название темы по её \a theme_id */
QString TrieSpellerResults::themeFullTitleById(const QString &theme_id) const
{
    return m_themeTitleById.value(theme_id);
}



/*!
    Возвращает список результатов по теме theme
 */
TrieSpellerResults::list_results TrieSpellerResults::results(const QString &theme) const
{
    return m_data.value(theme);
}

/*!
    Возвращает список результатов по полному названию темы \a theme_title
 */
TrieSpellerResults::list_results
    TrieSpellerResults::results_by_theme_title(const QString &theme_title) const
{
    return m_data.value(m_themeTitleById.key(theme_title));
}


/*!
    Возвращает, содержится ли узел \a node в результатах по теме \a theme.
*/
bool TrieSpellerResults::contains(const QString &theme, TrieCompiledNode *node) const
{
    list_results t = results(theme);
    foreach (TrieSpellerResults::Result result, t)
        if (result.node == node)
            return true;
    return false;
}

/*!
    Добавляет к результатам данные из другого списка результатов \a other.
 */
void TrieSpellerResults::unite(TrieSpellerResults *other)
{
    QStringList themes = other->themes();
    foreach (QString theme, themes) {
        list_results list = other->results(theme);
        m_data[theme].append(list);								// TODO: теряется сортировка
        while (m_data[theme].size() > m_top)                    // Сохраняем не более top подсказок
            m_data[theme].removeLast();
    }
}




/*!
    Выводит в Debug результаты.
 */
void TrieSpellerResults::print() const
{
    QStringList themesList = themes();
    foreach (QString theme, themesList) {
        qDebug() << "---------------- " << theme << "---------------- ";
        list_results list = results(theme);
        for (int i = 0; i < list.count(); i++)
            qDebug() << i+1 << ":" << list[i].node->fullPath() << " : " << list[i].rate;
    }
}






