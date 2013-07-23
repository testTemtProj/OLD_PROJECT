/*
 * SuggestService.cpp
 *
 *  Created on: 7 лип. 2009
 *      Author: Silver
 */

#include <QtXml>
#include <QTextStream>
#include <iostream>
#include <glog/logging.h>

#include "SuggestService.h"
#include "FixLayout.h"
#include "LingvoTools.h"
#include "TrieSpeller.h"


SuggestService::SuggestService()
    : m_totalProcessingTime(0),
      m_fixSpellingLight(false), m_fixSpellingFull(false), m_fixLayout(false),
      m_minQueryLenToSuggest(0), m_minQueryLenToFixSpellingLight(0),
      m_minQueryLenToFixSpellingFull(0), m_minQueryLenToFixLayout(0)
{
    m_cache.setMaxCost(1000);
    m_queriesCount = 0;
    m_cacheHits = 0;
    speller = new TrieSpeller;
}

SuggestService::~SuggestService() {
}



/**
 * Инициализация сервиса.
 */
bool SuggestService::init(int argc, char **argv)
{
    return parseCommandLineOptions(argc, argv);
}


/**
 * Разбор параметров сервиса из опций командной строки.
 */
bool SuggestService::parseCommandLineOptions(int argc, char **argv)
{
    /*
    if (argc < 3) {
        printUsage();
        return false;
    }
    */

    QString arg = argv[1];
    QString dictionaryFile;
    QString dictionaryKey;
    QString xmlSettings;

    if (arg.startsWith("--dictionary-file="))
        dictionaryFile = arg.split("--dictionary-file=").value(1);
    if (getenv("suggest_dictionary-file"))
        dictionaryFile = getenv("suggest_dictionary-file");

    if (arg.startsWith("--shared-key="))
        dictionaryKey = arg.split("--shared-key=").value(1);
    if (getenv("suggest_shared-key"))
        dictionaryKey = getenv("suggest_shared-key");

    if (arg.startsWith("--xml-settings="))
        xmlSettings = arg.split("--xml-settings=").value(1);
    if (getenv("suggest_xml-settings"))
        xmlSettings = getenv("suggest_xml-settings");

    if (!dictionaryFile.isEmpty()) {
        if (!speller->loadDictionaryFromFile(dictionaryFile)) {
            qDebug() << "Error loading dictionary from file!";
            qDebug() << "Failed dictionary details: ";
            qDebug() << "   File:" << dictionaryFile;
            return false;
        }
        return true;
    }

    if (!dictionaryKey.isEmpty()) {
        if (!speller->loadDictionaryFromSharedMemory(dictionaryKey)) {
            qDebug() << "Error loading dictionary from shared memory!";
            qDebug() << "Failed dictionary details: ";
            qDebug() << "    Key:" << dictionaryKey;
            return false;
        }
        return true;
    }

    if (!xmlSettings.isEmpty()) {
        return parseXmlSettings(xmlSettings);
    }

    printUsage();
    return false;
}

/**
 * Подсказка по пользованию аргументами командной строки.
 */
void SuggestService::printUsage()
{
    std::cout << "Usage: service --shared-key=[key] q=QUERY \n"
                 "   or: service --dictionary-file=[filename] q=QUERY\n"
                 "   or: service --xml-settings=[filename] q=QUERY\n";
}

/**
 * Разбор параметров сервиса из файла settings.xml
 */
bool SuggestService::parseXmlSettings(QString settingsFilename)
{
    // Чтение файла настроек
    if (settingsFilename.isEmpty())
        settingsFilename = qApp->applicationDirPath() + "/settings.xml";
    QFile f(settingsFilename);
    QDomDocument xmlSettings;
    if (!xmlSettings.setContent(&f)) {
        qDebug() << "Invalid settings.xml file!";
        return false;
    }

    // Читаем настройки сервиса
    QDomElement elSuggest = xmlSettings.documentElement().firstChildElement("Suggest");
    if (elSuggest.isNull()) {
        qDebug() << "Invalid settings.xml file (Suggest node not found)!";
        return false;
    }

    m_minQueryLenToSuggest = elSuggest.attribute("minQueryLen").toInt();
    if (!m_minQueryLenToSuggest) {
        qWarning() << "minQueryLen set to 0. This is unsafe settings, "
                      "using 1 instead.";
        m_minQueryLenToSuggest = 1;
    }
    m_cacheLongQueries = elSuggest.firstChildElement("CacheLongQueries").text() == "true";
    m_longQueryTime = elSuggest.firstChildElement("CacheLongQueries").attribute("minTime").toInt();
    m_logLongQueries = elSuggest.firstChildElement("LogLongQueries").text() == "true";
    m_queryTimeToLog = elSuggest.firstChildElement("LogLongQueries").attribute("minTime").toInt();

    QDomElement elSpellingLight = elSuggest.firstChildElement("FixSpellingLight");
    m_fixSpellingLight = (elSpellingLight.text() == "true");
    m_minQueryLenToFixSpellingLight =
            elSpellingLight.attribute("minQueryLen").toInt();

    QDomElement elSpellingFull = elSuggest.firstChildElement("FixSpellingFull");
    m_fixSpellingFull = (elSpellingFull.text() == "true");
    m_minQueryLenToFixSpellingFull =
             elSpellingFull.attribute("minQueryLen").toInt();

    QDomElement elFixLayout = elSuggest.firstChildElement("FixLayout");
    m_fixLayout = (elFixLayout.text() == "true");
    m_minQueryLenToFixLayout = elFixLayout.attribute("minQueryLen").toInt();

    QDomElement elDictionary = elSuggest.firstChildElement("Dictionaries")
            .firstChildElement("Dictionary");
    int dictionariesCount = 0;
    while (!elDictionary.isNull()) {
        QString dictionaryFile = elDictionary.text();
        QString dictionaryKey = elDictionary.attribute("sharedMemoryKey", "");

        if (!dictionaryFile.isEmpty() && !speller->loadDictionaryFromFile(dictionaryFile)) {
            qDebug() << "Error loading dictionary from file!";
            qDebug() << "Failed dictionary details: ";
            qDebug() << "   File:" << dictionaryFile;
            return false;
        }

        if (!dictionaryKey.isEmpty() && !speller->loadDictionaryFromSharedMemory(dictionaryKey)) {
            qDebug() << "Error loading dictionary from shared memory!";
            qDebug() << "Failed dictionary details: ";
            qDebug() << "    Key:" << dictionaryKey;
            return false;
        }

         dictionariesCount++;
        elDictionary = elDictionary.nextSiblingElement("Dictionary");
    }

    if (!dictionariesCount) {
        qDebug() << "At least one dictionary should be loaded!";
        return false;
    }

    return true;
}


/**
 * Обрабатывает запрос.
 *
 * Возможные параметры:
 *		q 				  -	строка запроса
 *		stats			  - статистика использования сервиса
 *
 *
 * Возвращает JSON следующего формата:
 *
 * 		[ {t: "Theme1", w: [["Word1", results, len, distance],
 * 		                    ["Word2", results2, len2], distance2]},
 * 		   ... ]
 *
 * где	results -- кол-во возможных окончаний данной подсказки,
 * 		len -- кол-во набранных символов,
 *              distance -- расстояние правки между реально набранным (но очищенным)
 *                          запросом и подсказкой. Фактически, количество ошибок,
 *                          исправленных для выдачи данной подсказки.
 *
 ***/
QString SuggestService::processQuery(const QString &queryString)
{
    QString res;
    QTime t;
    t.start();

    // Выделяем параметры
    QUrl url("localhost/suggest.fcgi?" + queryString);
    QString q = QUrl::fromPercentEncoding(url.queryItemValue("q").toUtf8()
                                          .replace("+", "%20"));

    QString r;
    if (!q.isEmpty())
    {
        checkDictionary();

        m_queriesCount++;
        QString qClean = TrieSpeller::cleanString(q);

        if (m_cacheLongQueries && m_cache.contains(qClean)) {
            m_cacheHits++;
            return *m_cache[qClean];
        }

        int len = qClean.length();
        if (len < m_minQueryLenToSuggest)
            return "[]";

        speller->config.fixLayout =
                m_fixLayout && len >= m_minQueryLenToFixLayout;
        speller->config.fixSpelling =
                m_fixSpellingFull && len >= m_minQueryLenToFixSpellingFull;
        speller->config.fixSpellingLight =
                m_fixSpellingLight && len >= m_minQueryLenToFixSpellingLight;
        speller->config.phoneticSort = true;

        TrieSpellerResults results = speller->suggest(q);
        r = SuggestionResultToJSON(results, q);

        int elapsed = t.elapsed();
        m_totalProcessingTime += elapsed;

        if (elapsed > m_longQueryTime) {
            m_longQueries.append(qMakePair(queryString, elapsed));

            if (m_cacheLongQueries)
                m_cache.insert(q, new QString(r));
        }

        LOG_IF(INFO, m_logLongQueries && elapsed > m_queryTimeToLog)
                << "Long query: \"" << q.toUtf8().data() << "\"\n"
                << "ms: " << t.elapsed() << "\n"
                << "qs: " << queryString.toUtf8().data();
    }

    if (url.queryItemValue("show") == "status")
        return status();

    return r;
}


QString row(const QString &label, const QVariant &value)
{
    return QString("<tr><td>%1</td><td>%2</td></tr>\n").arg(label).arg(value.toString());
}

/** Строка состояния сервиса. */
QString SuggestService::status() const
{
    QString status;
    QTextStream out(&status);

    // Header
    out << "<html>\n"
        "<head><meta http-equiv=\"content-type\" content=\"text/html; "
        "charset=UTF-8\">\n"
        "<style>\n"
        "body { font-family: Arial, Helvetica, sans-serif; }\n"
        "h1, h2, h3 {font-family: \"georgia\", serif; font-weight: 400;}\n"
        "table { border-collapse: collapse; border: 1px solid gray; }\n"
        "td { border: 1px dotted gray; padding: 5px; font-size: 10pt; }\n"
        "th {border: 1px solid gray; padding: 8px; font-size: 10pt; }\n"
        "</style>\n"
        "</head>\n";

    // General state
    int avgResponseTime_ms =
            m_queriesCount? (m_totalProcessingTime / m_queriesCount) : 0;
    out << "<body>\n";
    out << "<h1>SuggestService state info</h1>\n";
    out << "<table>" <<
        row("Version:",               version()) <<
        row("Total queries:",         m_queriesCount) <<
        row("Avg response time, ms:", avgResponseTime_ms) <<
        row("Cache state:",           m_cacheLongQueries? "on" : "off") <<
        row("Cache hits:",            m_cacheHits) <<
        row("Cache size:",            m_cache.size());

    // Dictionary info
    TrieCompiled *tree = speller->getTree();
    out <<
        row("Compiler name:",         tree->metaData("_compiler_name")) <<
        row("Compiler version:",      tree->metaData("_compiler_version")) <<
        row("Date compiled:",         tree->metaData("_date_compiled")) <<
        row("Terms count:",           tree->metaData("_terms_count")) <<
        row("Nodes count:",           tree->metaData("_nodes_count")) <<
        row("Source:",                tree->metaData("_source"));

    out << "</table>\n";

    out << "<h2>Long-running queries</h2>";
    out << "<table>" <<
        "<tr><th>Query string</th><th>Time, ms</th></tr>\n";
    QPair<QString, int> value;
    foreach (value, m_longQueries) {
        out << row(value.first, value.second);
    }
    out << "</table>";

    // Footer
    out << "</body>\n"
        << "</html>\n";

    return status;
}


/*!
    TODO: Проверка, не изменился ли словарь в разделямой памяти
*/
void SuggestService::checkDictionary()
{
    static QString dictionaryTimestamp;
    //if (dictionaryTimestamp.isNull())
}



/** Возвращает строку с JSON представлением подсказок */
QString SuggestService::SuggestionResultToJSON(const TrieSpellerResults &results,
                                               const QString &query)
{
    QString json;
    int top = 10;

    foreach (QString theme, results.themesOrdered()) {
        TrieSpellerResults::list_results nodes = results.results(theme);
        QMap<QString, bool> resultHasMore;
        QMap<QString, int> resultMatchLength;
        QMap<QString, int> resultEditDistance;
        QStringList resultStrings;

        if (nodes.isEmpty())
            continue;

//        QString localizedTheme = mapLocalizedThemes.value(theme);
//        if (localizedTheme.isEmpty())
//            localizedTheme = theme;         //".";
        QString localizedTheme = escapeJSON(results.themeFullTitleById(theme));

        json += "{t:\"" + localizedTheme + "\", w:[";
        int i = 0;
        int uniqueResults = 0;
        while ( (i < nodes.count()) && (uniqueResults < top) ) {
            TrieCompiledNode *n = nodes[i].node;
            QString text = n->fullPath();
            text.replace('_', ' '); // Показываем неразрывный пробел как обычный
            text.chop(1);

            //text += QString(" %1").arg(nodes[i].rate);

            // Имеет ли подсказка продолжение ("ещё")
            bool hasMore;								// TODO: long thing!
            if (n->parent().iterateToChild(' '))
                hasMore = true;
            else
                hasMore = false;

            if (!resultHasMore.contains(text)) {
                resultHasMore[text] = hasMore;
                resultStrings.append(text);
                uniqueResults++;
            }
            else if (hasMore)
                resultHasMore[text] = true;

            // Длина набранного текста
            QString match = nodes[i].match->fullPath();
            resultMatchLength[text] = match.length();

            // Редакционное расстояние между набранным текстом и реальной
            // подсказкой
            resultEditDistance[text] =
                LingvoTools::distance(match, results.query().left(match.length()));

            i++;
        }

        foreach (QString term, resultStrings) {
            int rate = resultHasMore.value(term)? 1 : 0;
            int editDistance = resultEditDistance[term];
            int highlightLen = resultMatchLength[term];

            json += QString("[\"%1\",%2,%3,%4],")
                    .arg(escapeJSON(term))
                    .arg(rate)
                    .arg(highlightLen)
                    .arg(editDistance);
        }

        json.chop(1);
        json += "]},";
    }

    json.chop(1);

    //	res.prepend("{t:\"elapsed\", w:[[\"" + QString::number(t.elapsed()) + "\",0,0]]},");
    json.prepend("[");
    json.append("]\n");

    return json;
}



/*!
    Возвращает безопасное JSON-представление строки
 */
QString SuggestService::escapeJSON(QString str)
{
    return str.replace("\\", "\\\\")
           .replace("\"", "\\\"")
           .replace("/", "\\/")
           .replace("\b", "\\b")
           .replace("\f", "\\f")
           .replace("\n", "\\n")
           .replace("\r", "\\r")
           .replace("\t", "\\t");
}
