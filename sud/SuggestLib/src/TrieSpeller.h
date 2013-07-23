/*
 * TrieSpeller.h
 *
 *  Created on: 26.08.2009
 *      Author: Silver
 */

#ifndef TRIESPELLER_H_
#define TRIESPELLER_H_


#include <QtCore>

#include "TrieCompiled.h"



/*!
    Настройки спеллера.
*/
struct TrieSpellerConfig {
    bool    fixLayout;              /// Исправлять раскладку (дштгч => linux)
    bool    fixSpelling;            /// Исправление орфографии
    bool    fixSpellingLight;       /// Исправление "лёгких" ошибок (а-о, е-и, нн-н и т.п.)
    int     minSpellingLen;         /// Минимальная длина запроса, начиная с которой начать исправлять
    bool    phoneticSort;           /// Сортировать результаты по фонетической близости
};


class TrieSpellerResults;


/*!
    Выдаёт подсказки по запросу. Может исправлять орфографию.
*/
class TrieSpeller
{
public:
    TrieSpeller();
    virtual ~TrieSpeller();

    bool loadDictionaryFromFile(const QString &filename);
    bool loadDictionaryFromSharedMemory(const QString &key);
    bool loadDictionaryFromRawData(const char *data);

    void SuggestAll(const QString &query, node_list &result_suggestions,
                    bool &is_misspelled, node_list &matches);
    TrieSpellerResults suggest(const QString &word, bool fix = true, int top = 10);

    TrieSpellerResults GroupNodesByThemes(const node_list &nodes, int top,
                                          const QString &word,
                                          bool phoneticSort,
                                          const node_list &matches);
    void ExpandSuggestions(TrieSpellerResults &results, int top = 10);

    TrieSpellerConfig config;

    static QString cleanString(const QString &str);
    static QString escapeSpaces(const QString &str);

    TrieCompiled *getTree() { return tree; }

private:

    void removeDuplicateNodes(node_list &nodes, node_list *matches = 0);
    bool SearchMisspeled(const QString &query, node_list &nodes);
    void CompleteWords(const node_list &nodes, node_list &suggestedNodes,
                       node_list &matches);
    void ExpandResultsOneTheme(TrieSpellerResults &mainResults, int limit,
                               const QString &theme, bool expandAll);
    void ExpandSingleSuggestions(TrieSpellerResults &results,
                                 const QString &theme);

    int CountersRateData(TrieCompiledNode *n, const QString &theme);
    int CountersCountData(TrieCompiledNode *n, const QString &theme);
    int ParseCountersData(const QString &data, const QString &theme) const;
    int ParseRateData(const QString &data, const QString &theme) const;

    QString mapToString(QMap <QString, int> map);
    QMap <QString, int> stringToMap(const QString &str);
    QString simpleMisspellsPattern(const QString &str);
    bool loadThemesList();
    bool fixLayout(QString &str);

    TrieCompiled *tree;
    QMap<QString,QString> mapThemes;
    QMap<QString,QString> mapLocalizedThemes;
    QBuffer buffer;
    QSharedMemory shared;

    enum {
        RateData = 0,
        CountData = 1
    };
};


/*!
    Хранение и обработка списка результатов
*/
class TrieSpellerResults
{
public:

    struct Result
    {
        Result(TrieCompiledNode *node = 0, int rate = 0,
               TrieCompiledNode *match = 0)
            : node(node), rate(rate), match(match) {}

        TrieCompiledNode *node;
        int rate;
        TrieCompiledNode *match;
    };

    typedef QList<TrieSpellerResults::Result> list_results;

    void add(const QString &theme, TrieCompiledNode *node, int rate,
             TrieCompiledNode *match);
    void add(TrieCompiledNode *node, TrieCompiledNode *match);
    void remove(const QString &theme, TrieCompiledNode *node);
    void print() const;

    /*! Возвращает список тем, задействованных в результатах */
    QStringList themes() const;

    /*! Возвращает список тем, отсортированных по суммарному рейтингу (в порядке
        убывания) */
    QStringList themesOrdered() const;

    /*! Возвращает полное название темы по её \a theme_id */
    QString themeFullTitleById(const QString &theme_id) const;

    /*! Возвращает список результатов по теме \a theme. */
    list_results results(const QString &theme) const;

    /*! Список результатов по полному названию темы \a theme_title */
    list_results results_by_theme_title(const QString &theme_title) const;

    /*! Добавляет к результатам данные из другого списка результатов
        \a other */
    void unite(TrieSpellerResults *other);

    /*! Возвращает, содержится ли узел \a node в результатах по теме \a theme */
    bool contains(const QString &theme, TrieCompiledNode *node) const;

    /*! Возвращает запрос, по которому были получены подсказки. */
    QString query() const { return m_query; }

    void setTop(int top) {
        m_top = top;
    }
    int top() const {
        return m_top;
    }


private:
    void insertSorted(list_results &list, TrieCompiledNode *n, int rate,
                      TrieCompiledNode *match);

    QMap<QString, list_results> m_data;
    QMap<QString, QString> m_themeTitleById;
    int m_top;
    QString m_query;
    bool m_phoneticSort;

private:
    TrieSpellerResults(QMap<QString, QString> themeTitleById, int top,
                       const QString &query, bool phoneticSort);

    friend class TrieSpeller;
};





#endif /* TRIESPELLER_H_ */
