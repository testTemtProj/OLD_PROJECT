/*
 * LingvoTools.h
 *
 *  Created on: 16 черв 2009
 *      Author: Silver
 */

#ifndef LINGVOTOOLS_H_
#define LINGVOTOOLS_H_

#include <QtCore>

class LingvoTools {
public:
    LingvoTools();
    virtual ~LingvoTools();

//	QStringList suggest(const QString &word);

    static QStringList wordCombinations(const QString &w);
    static QString simplifyString(QString str, QString &charLength);
    static int distance(const QString &word1, const QString &word2);
    static int distancePhonetic(const QString &word1, const QString &word2);
    static unsigned int termRate(const QString &term);
    static int intersectLength(const QString &s1, const QString &s2);

    QString getStem(const QString &word, bool reportError = false );
    void loadDictionary(QIODevice *device);
    void loadDictionary(const QString &filename);
    void loadWikiTitles(const QString &filename);
    bool inDictionary(const QString &word);
    bool inWikiTitles(const QString &word);


    enum EditCosts {
        COST_LIGHT_REPLACEMENT = 3,
        COST_HEAVY_REPLACEMENT = 10,
        COST_EDIT = 10,
        COST_SWAP = 10,
        COST_WORD_BEGINNING_PENALITY = 2,
        WORD_BEGINNING_CHARS
    };



private:
    QStringList m_stems;							// Список ключевых слов
    QHash <QString, int> m_dict;					// Карта всех слов с ссылкой на m_stems
    QStringList m_wiki;								// Список названий статей Википедии

    static int characterReplacementWeight(QChar c1, QChar c2);

};

#endif /* LINGVOTOOLS_H_ */
