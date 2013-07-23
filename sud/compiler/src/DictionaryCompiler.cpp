#include <QTextCodec>
#include <QPair>
#include <QStringList>
#include <QDateTime>
#include <QSet>
#include <QMap>
#include "DictionaryCompiler.h"

DictionaryCompiler::DictionaryCompiler()
    : use_non_breaking_spaces(true),
      themes_count_(0), success_count_(0), skipped_count_(0)
{
}

void DictionaryCompiler::AddTerm(const QString &term,
                                 const QString &theme_title,
                                 int rate)
{
    QString theme_id = GetThemeId(theme_title);

    Entry entry;
    entry.term = CleanString(term);
    entry.theme_id = theme_id;
    entry.rate = rate;

    entries_.append(entry);
}


void DictionaryCompiler::AddMetaData(const QString &key, const QString &value)
{
    builder_.setMetaData(key, value);
}


void DictionaryCompiler::Compile(QFile &out)
{
    if (use_non_breaking_spaces) {
        SortEntries();
        DetectNonbreakingSpaces();
    }

    CompileEntries();
    WriteServiceMetadata();
    builder_.save(out);
    out.close();
}


QString DictionaryCompiler::GetThemeId(const QString &theme_title)
{
    QString theme_id;

    if (theme_to_id_.contains(theme_title))
        theme_id = theme_to_id_[theme_title];
    else {
        theme_id = QString::number(themes_count_++);
        theme_to_id_[theme_title] = theme_id;
    }

    return theme_id;
}


void DictionaryCompiler::CompileEntries()
{
    int len = entries_.size();
    for (int i = 0; i < len; i++) {
        bool ok = CompileEntry(entries_[i]);
        if (ok)
            success_count_++;
        else
            skipped_count_++;
    }
}


bool DictionaryCompiler::CompileEntry(const Entry &entry)
{
    static QTextCodec *codec = QTextCodec::codecForName("Windows-1251");
    if (!codec->canEncode(entry.term))
        return false;

    QByteArray decoded = codec->fromUnicode(entry.term);
    BuilderNode *n = builder_.root();
    foreach (char ch, decoded) {
        n = builder_.addNode(ch, n);
        if (ch == ' ')
            UpdateCounters(n, entry.theme_id, entry.rate);
    }

    n = builder_.addNode(end_of_line, n);
    UpdateCounters(n, entry.theme_id, entry.rate);
    return true;
}

// Словарь счётчиков
typedef QMap<QString, QPair<int, int> > CountersMap;

/** Преобразует словарь счётчиков в строку */
QString countersToString(const CountersMap &counters)
{
    QString res;
    for (CountersMap::const_iterator i = counters.constBegin();
                                     i != counters.constEnd();
                                     i++)
    {
        res += i.key();
        res += ":";
        res += QString::number(i.value().first);
        res += ":";
        res += QString::number(i.value().second);
        res += ";";
    }
    res.chop(1);            // Последний символ ';'
    return res;
}


/** Преобразует строку в словарь счётчиков. */
CountersMap stringToCounters(const QString &str)
{
    CountersMap res;
    QStringList themes = str.split(";", QString::SkipEmptyParts);
    foreach (QString row, themes) {
        QString theme = row.section(':', 0, 0);
        int count = row.section(':', 1, 1).toInt();
        int rate = row.section(':', 2, 2).toInt();
        res[theme] = qMakePair(count, rate);
    }
    return res;
}

/** Обновляет счётчики узла \a n.
 *
 * Разделители слов и окончания фраз хранят информацию о том, сколько за данным
 * узлом будет следовать результатов по каждой тематике и какой суммарный
 * рейтинг этих результатов.
 *
 * Счётчики храняться в пользовательских данных узла в следующем формате:
 *
 * theme1:n1:r1;theme2:n2:r2;...
 *
 * Например, для узла, за которым будут следовать 5 результатов по
 * автомобильной тематике с общим весом 200, и 1 результат по тематике
 * "Прочее" весом 30, пользовательские данные будут выглядеть так:
 *
 * auto:5:200;other:1:30
 *
 */
void DictionaryCompiler::UpdateCounters(BuilderNode *n,
                                        const QString &theme_id,
                                        int rate)
{
    CountersMap counters = stringToCounters(n->data());
    counters[theme_id].first  += 1;
    counters[theme_id].second += rate;
    n->setData(countersToString(counters).toAscii());
}

/** Очищает строку от недопустимых символов */
QString DictionaryCompiler::CleanString(const QString &str)
{
    QString t = str.toLower();

    t.replace(QRegExp("[^\\w/\\\\_]"), " ");
    return t.simplified();
}


void DictionaryCompiler::SortEntries()
{
    qSort(entries_.begin(), entries_.end());
}


void DictionaryCompiler::DetectNonbreakingSpaces()
{
    QMap<QString, QSet<QString> > conts;

    // Строим варианты продолжения по каждому префику
    foreach (const Entry &entry, entries_) {
        QStringList words = entry.term.split(' ');
        QString prefix;

        for (int i = 0; i < words.size() - 1; i++) {
            if (i == 0)
                prefix = words[i];
            else
                prefix += ' ' + words[i];

            conts[prefix].insert(words[i + 1]);
        }
    }

    // Расставляем неразрывные пробелы, если за словом идёт только
    // один вариант продолжения
    int len = entries_.size();
    for (int entry_index = 0; entry_index < len; entry_index++) {
        Entry &entry = entries_[entry_index];
        QStringList words = entry.term.split(' ');
        QString prefix;
        QString processed;

        for (int i = 0; i < words.size() - 1; i++) {
            if (i == 0)
                prefix = words[i];
            else
                prefix += ' ' + words[i];

            bool is_hard_space = (conts[prefix].size() <= 1);
            char delim = is_hard_space? non_breaking_space : ' ';
            processed += words[i] + delim;
        }

        processed += words[words.size() - 1];
        entry.term = processed;
    }
}


void DictionaryCompiler::WriteServiceMetadata()
{
    builder_.setMetaData("_compiler_name", QByteArray(CompilerName()));
    builder_.setMetaData("_compiler_version", QByteArray(Version()));
    builder_.setMetaData("_terms_count", QString::number(success_count_));
    builder_.setMetaData("_date_compiled", QDateTime::currentDateTime()
                                                      .toString(Qt::ISODate));
    builder_.setMetaData("_nodes_count", QString::number(builder_.nodeCount()));
    QStringList themes;
    foreach (QString theme_title, theme_to_id_.keys()) {
        themes.append(theme_to_id_[theme_title] + ":" + theme_title);
    }
    builder_.setMetaData("_themes", themes.join("\n"));
}

