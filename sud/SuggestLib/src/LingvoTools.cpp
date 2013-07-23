/*
 * LingvoTools.cpp
 *
 *  Created on: 16 черв 2009
 *      Author: Silver
 */

//#include <QtSql>

#include "LingvoTools.h"

LingvoTools::LingvoTools() {
    // TODO Auto-generated constructor stub

}

LingvoTools::~LingvoTools() {
    // TODO Auto-generated destructor stub
}




///*
// * Предлагает варианты исправления слова
// */
//QStringList LingvoTools::suggest(const QString &word)
//{
//
//	QStringList combinationsOne = wordCombinations(simplifyString(word));
//	QStringList combinations;
//	for (int i = 0; i < combinationsOne.size(); i++)
//		combinations += wordCombinations(combinationsOne[i]);
//	combinations += combinationsOne;
//	combinations.removeDuplicates();
//	qDebug() << combinations.size() << "комбинаций: " << combinations;
//
//
//	QString sqlComb;
//	int i = 0;
//	foreach(QString str, combinations) {
//		sqlComb += "'" + combinations[i] + "',";
//		i++;
//	}
//	sqlComb.chop(1);
//	QSqlQuery q;
//	if (!q.prepare("select distinct word from misspellings where misspell in (" + sqlComb + ") "
//					" order by rate desc")) {
//		qDebug() << "Ошибка подготовки запроса!";
//		return QStringList();
//	}
//	if (!q.exec()) {
//		qDebug() << "Ошибка выполнения запроса!";
//		return QStringList();
//	}
//
//	QStringList result;
//	while (q.next())
//		result << q.value(0).toString();
//	return result;
//
//}

/*
 * Упрощает строку
 * - приводит всё к нижнему регистру
 * - удаляет двойные буквы
 * - оглушает согласные.
 * - выкидывает знаки препинания
 *
 * В charLength возвращает "ширину" каждого символа полученной строки.
 * Например, для "неожиданно, он" функция вернёт
 *               "ниожидоно он",  а charLength будет
 *               "111111112211"
 */
QString LingvoTools::simplifyString(QString str, QString &charLength)
{
//	return str;									// DEBUG!


    QString res;
    QChar prev;
    int charlen = 0;
    QRegExp r("[\\w ]");				// буквы, пробел
    charLength = "";

    str = str.toLower();

    for (int i = 0; i < str.length(); i++) {
        charlen++;

        if (r.indexIn(QString(str[i])) > -1) {					// Если не знак препинания
            if (str[i] != prev) {
                res += str[i];
                charLength.append(QString::number(charlen));
                charlen = 0;
            }

            prev = str[i];
        }
    }

    /*	if (charlen) {												// Добавляем последний символ
                charlen += charLength.right(1).toInt();
                charLength.chop(1);
                charLength.append(QString::number(charlen));
        }
    */
    QList <QChar> trFrom;
    QList <QChar> trTo;
    QString wordStart = res.left(2);
    res = res.remove(0, 2);									// Первые две буквы должны совпадать

    trFrom << 'з' << 'а' << 'в' << 'б' << 'е';
    trTo   << 'с' << 'о' << 'ф' << 'п' << 'и';
    Q_ASSERT( trFrom.count() == trTo.count());

    for (int i = 0; i < trFrom.count(); i++) {
        res = res.replace(trFrom[i], trTo[i]);
    }

    res = wordStart + res;

    return res;
}


/*!
 * Возвращает список всех слов, полученных изменением исходного слова word
 */
QStringList LingvoTools::wordCombinations(const QString &word)
{
    QStringList res;
    int len = word.length();
    int i;

    // Варианты слова со вставленной, удалённой и изменёнными буквами
    for (i = 0; i < len; i++) {
        res += QString(word).insert(i, '.');
        res += QString(word).replace(i, 1, '.');
        res += QString(word).remove(i, 1);          // TODO: Было закоменчено. Возможно, точка должна также обозначать отсутствие символа.
    }
    res += QString(word).insert(len, '.');

    // Варианты перестановки букв местами
    for (i = 0; i < len - 1; i++) {
        QString s = word;
        QChar t = s[i];
        s[i] = s[i + 1];
        s[i + 1] = t;
        res += s;
    }

    return res;

}




/*
 * Возвращает расстояние Левенштейна между словами word1 и word2
 */
int LingvoTools::distance(const QString &word1, const QString &word2)
{
    int l1 = word1.size(), l2 = word2.size();
    int d[250][250];

    int i, j, cost;

    for (i=0; i<=l1; i++)
        d[i][0] = i;
    for (j=1; j<=l2; j++)
        d[0][j] = j;

    for (i=1; i<=l1; i++)
        for (j=1; j<=l2; j++) {
            cost = (word1[i-1] == word2[j-1])? 0 : 1;

            int min = qMin( d[i-1][j] + 1,
                            d[i][j-1] + 1);
            min = qMin (min, d[i-1][j-1] + cost);

            if ((i>1) && (j>1) && (word1[i-1] == word2[j-2]) && (word1[i-2] == word2[j-1])) {
                min = qMin( min, d[i-2][j-2] + cost);
            }

            d[i][j] = min;
//			if (min > diff)
//				return diff+1;
        }

    return d[l1][l2];

}


/** Цена замена сивола \a c1 на \a c2. */
int LingvoTools::characterReplacementWeight(QChar c1, QChar c2)
{
    static QChar ru_A = QChar(0x0430);
    static QChar ru_O = QChar(0x043E);
    static QChar ru_S = QChar(0x0441);
    static QChar ru_Z = QChar(0x0437);
    static QChar ru_E = QChar(0x0435);
    static QChar ru_I = QChar(0x0438);
//    static QChar ru_N = QChar(0x043d);
//    static QChar ru_T = QChar(0x0442);

    if (c1 == c2)
        return 0;

    if ( (c1 == ' ' && c2 == '_') ||
         (c1 == '_' && c2 == ' '))
         return 0;

    if ( (c1 == ru_A && c2 == ru_O) ||
         (c1 == ru_O && c2 == ru_A) ||
         (c1 == ru_S && c2 == ru_Z) ||
         (c1 == ru_Z && c2 == ru_S) ||
         (c1 == ru_I && c2 == ru_E) ||
         (c1 == ru_E && c2 == ru_I)
         )
        return COST_LIGHT_REPLACEMENT;

    else
        return COST_HEAVY_REPLACEMENT;
}

/**
 * Возвращает фонетическую близость между словами \a word1 и \a word2.

Фонетическая близость похожа на расстояние Левенштейна, но со следующими
различиями:

1. Вставка, удаление или замена символа считаются за 10 очков.

2. Ошибки "лёгкой" орфографии (а-о, и-е, с-з) считаются за 5 очков.

3. Ошибки в первых трёх буквах слова штрафуются тремя очками.

4. Обычный и неразрывный пробел считаются одним и тем же символом

 */
int LingvoTools::distancePhonetic(const QString &word1, const QString &word2)
{
    int l1 = word1.size(), l2 = word2.size();
    int d[250][250];

    int i, j, cost;

    for (i=0; i<=l1; i++)
        d[i][0] = i;
    for (j=1; j<=l2; j++)
        d[0][j] = j;

    for (i=1; i<=l1; i++)
        for (j=1; j<=l2; j++) {

            // Пенальти за опечатку в первых трёх буквах слова
            cost = LingvoTools::characterReplacementWeight(word1[i-1], word2[j-1]);

            bool at_word_beginning = (i <= WORD_BEGINNING_CHARS || j <= WORD_BEGINNING_CHARS);
            int penalty = (cost && at_word_beginning)? COST_WORD_BEGINNING_PENALITY : 0;

            int min = qMin( d[i-1][j] + COST_EDIT + penalty,
                            d[i][j-1] + COST_EDIT + penalty);
            min = qMin (min, d[i-1][j-1] + cost + penalty);

            if ((i>1) && (j>1) && (word1[i-1] == word2[j-2]) && (word1[i-2] == word2[j-1])) {
                min = qMin( min, d[i-2][j-2] + COST_SWAP + penalty);
            }

            d[i][j] = min;
        }

    return d[l1][l2];

}




/*
 * Загружает словарь
 */
void LingvoTools::loadDictionary(QIODevice *device)
{
    qDebug() << "Starting" << Q_FUNC_INFO;
    QTime t;
    t.start();

    m_dict.clear();
    m_stems.clear();

    if (!device->isOpen())
        if (!device->open(QIODevice::ReadOnly)) {
            qDebug() << "Ошибка загрузки словаря!";
            return;
        }
    QTextStream in(device);
    int stemIndex = -1;

    while (!in.atEnd()) {
        QStringList words = in.readLine().toLower().replace("ё", "е").split(' ', QString::SkipEmptyParts);
        QString stem = words[0];						// Ключевое слово (в именительном падеже)
        stemIndex++;
        unsigned int stemRate = termRate(stem);
        int wordsCount = words.count();
        m_stems.append(stem);
        for (int i = 0; i < wordsCount; i++) {
            if (m_dict.contains(words[i]))
                if (termRate(m_stems.at(m_dict[words[i]])) > stemRate)
                    continue;
            m_dict[words[i]] = stemIndex;
        }
    }

    qDebug() << "Dictionary loaded in" << t.elapsed() << "ms";
}

/*
 * Загружает словарь из файла filename.
 * Метод для удобства.
 */
void LingvoTools::loadDictionary(const QString &filename)
{
    QFile file(filename);
    loadDictionary(&file);

}
/*
 * Возвращает слово word в нормальной форме (именительный падеж, единственное число).
 * Если слово не содержится в словаре, то при reportError == true возвращает QString(),
 * при reportError == false возвращает word
 */
QString LingvoTools::getStem(const QString &word, bool reportError)
{
    if (!m_dict.contains(word))
        return reportError? QString() : word;
    return m_stems.at(m_dict[word]);
}



/*
 * Возвращает рейтинг term среди запросов.
 */
unsigned int LingvoTools::termRate(const QString &term)
{
    return 1;			// TODO: dummy!


    /***  * commented: 14 apr 2011

    static QString lastTerm = "";
    static unsigned int lastTermRate = 0;

    if (term == lastTerm)
        return lastTermRate;

    QSqlQuery q;
    q.prepare("select rate_1 from term_stats where term = ?");
    q.addBindValue(term);
    q.exec();
    if (q.next())
        lastTermRate = q.value(0).toInt();
    else
        lastTermRate = 0;

    lastTerm = term;
    return lastTermRate;
    */
}




/*
 * Проверяет наличие слова word в словаре.
 */
bool LingvoTools::inDictionary(const QString &word)
{
    return m_dict.contains(word);
}


/*
 * Проверяет наличие слова word в Википедии.
 */
bool LingvoTools::inWikiTitles(const QString &word)
{
    return m_wiki.contains(word);
}


/*
 * Загружает в словарь название статей Википедии (только первые слова)
 */
void LingvoTools::loadWikiTitles(const QString &filename)
{
    /***
    QBoy silver;
    QGirl svet;
    if (!silver.fuck(&svet, Qt::Pose69, true)) {
        qDebug() << "";
        return false;
    }
    return true;


    ***/

    qDebug() << "Starting" << Q_FUNC_INFO;
    QFile f(filename);
    if (!f.open(QFile::ReadOnly)) {
        qDebug() << "Ошибка открытия файла" << filename;
        return;
    }
    QTextStream stream(&f);

    QString s;
    QString prev;
    while (!stream.atEnd()) {
        s = stream.readLine().split("_").value(0);
        s = s.toLower().replace("ё", "е");
        if (s != prev) {
            m_wiki << s;
            prev = s;
        }
    }
    qDebug() << "Загружено " << m_wiki.count() << "определений Википедии";
}



/*
 * Возвращает длину, на которую входит строка s1 в строку s2
 * (используя simplified представления)
 */
int LingvoTools::intersectLength(const QString &s1, const QString &s2)
{
    QString l;
    QString str1 = simplifyString(s1, l);
    QString str2 = simplifyString(s2, l);

//	qDebug() << Q_FUNC_INFO;
//	qDebug() << str1 << s1;
//	qDebug() << str2 << s2;
//	qDebug() << l;

    int res = 0;
    int i = 0;
    while ((i < str1.length()) && (i < str2.length()) && (str1.at(i) == str2.at(i))) {
        res += QString(l[i]).toInt();
        i++;
    }

    // Добавляем последние повторяющиеся буквы
    /*i = res ;
    QChar last = s2.at(i-1).toLower();
    //    i--;
    while ((i < s2.length()) && (last == s2.at(i).toLower())) {
        res++;
        i++;
        qDebug() << "Added 1";
    }
    */
    return res;
}
