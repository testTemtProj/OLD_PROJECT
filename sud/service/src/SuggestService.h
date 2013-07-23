/*
 * SuggestService.h
 *
 *  Created on: 7 лип. 2009
 *      Author: Silver
 */

#ifndef SUGGESTSERVICE_H_
#define SUGGESTSERVICE_H_

#include "TrieSpeller.h"


class SuggestService {
public:
    SuggestService();
    virtual ~SuggestService();

    bool init(int argc, char **argv);
    QString processQuery(const QString &queryString);
    void checkDictionary();
    QString SuggestionResultToJSON(const TrieSpellerResults &result,
                                   const QString &query);

    typedef QPair<QString, double> Suggest;								// (term, rate)
    typedef QList <Suggest> SuggestList;

    const char *version() const { return "0.3.1"; }

private:
    TrieSpeller *speller;
    QCache<QString, QString> m_cache;

    int m_longQueryLen;
    int m_queriesCount;             // Кол-во обработанных службой запросов
    int m_cacheHits;                // Кол-во попаданий в кеш
    bool m_logLongQueries;          // Нужно ли записывать долгие запросы в лог
    int m_queryTimeToLog;           // Время в мс, после которого запрос будет записан в лог
    bool m_cacheLongQueries;        // Нужно ли кешировать долгие запросы
    int m_longQueryTime;            // Время в мс, после которого запрос считается "долгим"
    unsigned long m_totalProcessingTime;         // Общее время обработки (для статистики)
    QList<QPair<QString, int> > m_longQueries;   // Список пар (запрос, время) долгих запросов

    // "Лёгкая" коррекция орфографии включена
    bool m_fixSpellingLight;

    // "Тяжёлая" коррекция орфографии включена
    bool m_fixSpellingFull;

    // Исправление раскладки клавиатуры
    bool m_fixLayout;

    // Минимальное количество символов, начиная с которого начинает работать служба
    int m_minQueryLenToSuggest;

    // Минимальная длина запроса, начиная с которой включается "лёгкая"
    // коррекция орфографии
    int m_minQueryLenToFixSpellingLight;

    // Минимальная длина запроса, начиная с которой включается "тяжёлая"
    // коррекция орфографии
    int m_minQueryLenToFixSpellingFull;

    // Минимальная длина запроса, начиная с которой включается исправление
    // раскладки клавиатуры
    int m_minQueryLenToFixLayout;

    bool parseCommandLineOptions(int argc, char **argv);
    bool parseXmlSettings(QString settingsFilename);
    void printUsage();
    QString status() const;
    QString escapeJSON(QString str);
};

#endif /* SUGGESTSERVICE_H_ */
