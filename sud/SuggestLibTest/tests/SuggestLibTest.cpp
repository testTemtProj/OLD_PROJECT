#include <QtTest/QtTest>
#include <QTextCodec>
#include <QTemporaryFile>
#include <QProcess>

#define private public
#include "TrieSpeller.h"
#undef private

#include "FixLayout.h"
#include "LingvoTools.h"


/** Вспомогательные класс для компиляции словаря во временный файл.

    Если \a autoRemove равен true, файл будет удалён после уничтожения объекта.
*/
class CompiledDictionary {
public:
    CompiledDictionary(const QStringList &dictionary, bool autoRemove = true)
    {
        f.setAutoRemove(autoRemove);

        if (!f.open())
            QFAIL("Error creating temporary file for the dictionary");
        CompileDictionary(f.fileName(), dictionary);
    }

    /** Компилирует список слов \a dictionary в файл \a filename */
    void CompileDictionary(const QString &filename,
                                           const QStringList &dictionary)
    {
        QProcess compiler;
        QString compiler_path = FindCompiler();
        if (compiler_path.isEmpty())
            QFAIL("Couldn't find dictionary compiler!");
        compiler.start(compiler_path, QStringList() << "--disable-non-breaking-spaces" << filename);
        if (!compiler.waitForStarted())
            QFAIL("Couldn't run dictionary compiler!");
        compiler.write(dictionary.join("\n").toUtf8());
        compiler.closeWriteChannel();
        if (!compiler.waitForFinished())
            QFAIL("waitForFinished() failed after compiling dictionary");
        QCOMPARE(compiler.exitCode(), 0);
    }

    /** Ищет компилятор словарей.
     *
     *  Возвращает путь к исполняемому файлу или пустую строку, если компилятор
     *  не найден. */
    QString FindCompiler() const
    {
        QStringList candidates = QStringList()
                                    <<  "../../compiler/bin/compiler"
                                    <<  "../compiler/bin/compiler"
                                    <<  "./compiler/bin/compiler";
        foreach (QString candidate, candidates)
            if (QFile::exists(candidate))
                return candidate;

        return QString();
    }


    QString fileName() const { return f.fileName(); }

private:
    QTemporaryFile f;
};



class TestSuggestLib : public QObject
{
    Q_OBJECT

public:
    TestSuggestLib()
    {
        QTextCodec::setCodecForCStrings(QTextCodec::codecForName("UTF-8"));
    }

    virtual ~TestSuggestLib() { }

private slots:
    void test_SearchMisspeled();
    void test_ConvertLayout();
    void test_CompleteWords();
    void test_ThemeGrouping();
    void test_ExpandSuggestions();
    void test_RemoveFullyExpandedSuggestion();
    void test_ExpandSuggestionsToEnd();
    void test_SuggestWholeWord();
    void test_NonbreakingSpace();
    void test_MisspeledSuggestSimpleSpeller();
    void test_MisspeledSuggestFullSpeller();
    void test_CyrilicQueries();
    void test_CountersData();
    void test_QueryInFirstChainNode();
    void test_RemoveDuplicatedSuggestions();
    void test_RemoveDuplicateNodes();
    void test_SuggestionSortings();
    void test_Matches();
    void test_HighlightSimpleCase();
    void test_HighlightSpellingCorrectionsCase1();
    void test_HighlightSpellingCorrectionsCase2();
    void test_HighlightFixedLayout();

    void test_EditDistance();
    void test_PhoneticDistance();

private:
    /** Функция для удобства проверки результатов \a results.

        TODO: Заменить макросом для более красивых сообщениях об ошибках QtTest.

        \param results   Список результатов по одной тематике
        \param expected  Список ожидаемые результатов. Каждая строка должна
                         быть в формате "ожидаемая подсказка \t рейтинг"
                         Если рейтинг не указан, он не проверяется. */
    void CheckResults(const TrieSpellerResults::list_results &results,
                      const QStringList &expected)
    {
        QCOMPARE(results.size(), expected.size());
        for (int i = 0; i < results.size(); ++i) {
            QString expected_term  = expected[i].section('\t', 0, 0);
            QString rate_str = expected[i].section('\t', 1, 1);
            QCOMPARE(results[i].node->fullPath(), expected_term);
            if (!rate_str.isEmpty()) {
                int expected_rate = rate_str.toInt();
                QCOMPARE(results[i].rate, expected_rate);
            }
        }
    }

    /** Проверяет список набранного */
    void CheckMatches(const TrieSpellerResults::list_results &results,
                      const QStringList &expected_matches)
    {
        QCOMPARE(results.size(), expected_matches.size());
        for (int i = 0; i < results.size(); ++i)
            QCOMPARE(results[i].match->fullPath(), expected_matches[i]);
    }

    /** Проверяет, что все результаты \a results нашлись по одному и тому же
        соответствию \a match. */
    void CheckAllMatches(const TrieSpellerResults::list_results &results,
                         const QString &expected_match)
    {
        for (int i = 0; i < results.size(); ++i) {
            QString match = results[i].match->fullPath();

            if (match != expected_match) {
                QString msg("Result #%1: \n"
                            "Actual:   %2\n"
                            "Expected: %3");
                msg = msg.arg(i + 1)
                         .arg(QString(match.toUtf8().toHex()))
                         .arg(QString(expected_match.toUtf8().toHex()));
                QFAIL(msg.toUtf8().data());
            }
        }
    }

    /** Сравнивает список узлов со списком строк. */
    void CheckNodeList(const node_list &nodes, const QStringList &expected)
    {
        QCOMPARE(nodes.size(), expected.size());

        for (int i = 0; i < nodes.length(); ++i) {
            QString fullPath = nodes[i]->fullPath();
            if (fullPath != expected[i]) {
                QString msg("Node #%1: \n"
                            "Actual:   %2\n"
                            "Expected: %3");
                msg = msg.arg(i + 1).arg(fullPath).arg(expected[i]);
                QFAIL(msg.toUtf8().data());
            }
        }
    }
};



void TestSuggestLib::test_SearchMisspeled()
{
    TrieSpeller speller;
    CompiledDictionary dictionary(QStringList() <<
                                  "ab" <<
                                  "ac" <<
                                  "z");
    bool load_result = speller.loadDictionaryFromFile(dictionary.fileName());
    QVERIFY(load_result);
    {   // Поиск правильного запроса без исправления опечаток
        node_list nodes;
        speller.config.fixSpelling = false;
        speller.SearchMisspeled("ab", nodes);
        QCOMPARE(nodes.length(), 1);
    }
    {   // Поиск правильного запроса с исправлением опечаток
        node_list nodes;
        speller.config.fixSpelling = true;
        speller.SearchMisspeled("ab", nodes);
        QCOMPARE(nodes.length(), 1);
    }
    {   // Поиск неправильного запроса без исправления опечаток
        node_list nodes;
        speller.config.fixSpelling = false;
        speller.SearchMisspeled("aq", nodes);
        QCOMPARE(nodes.length(), 0);
    }
    {   // Поиск неправильного запроса с исправлением опечаток
        node_list nodes;
        speller.config.fixSpelling = true;
        speller.SearchMisspeled("aq", nodes);
        QCOMPARE(nodes.length(), 3);        // Должно найтись: ab, ac, a
    }
    {   // Поиск правильного запроса в неправильной раскладке
        node_list nodes;
        speller.config.fixSpelling = false;
        speller.config.fixLayout = true;
        speller.SearchMisspeled("фи", nodes);
        QCOMPARE(nodes.length(), 1);
    }
    {   // TODO: Поиск неправильного запроса в неправильной раскладке
//        node_list nodes;
//        speller.config.fixSpelling = true;
//        speller.config.fixLayout = true;
//        speller.SearchMisspeled("фй", nodes);
//        QCOMPARE(nodes.length(), 2);
    }
}


/** Проверка перевода строки из одной раскладки в другую */
void TestSuggestLib::test_ConvertLayout()
{
    FixLayout fix;
    QCOMPARE( QString("привет"), fix.convertLayout("ghbdtn") );
    QCOMPARE( QString("борода"), fix.convertLayout(",jhjlf") );
    QCOMPARE( QString("hello"),  fix.convertLayout("руддщ")  );
}


/** Проверка дополнения до ближайшего слова */
void TestSuggestLib::test_CompleteWords()
{
    CompiledDictionary dictionary(QStringList() <<
                      "gettext" <<
                      "gettext source" <<
                      "gettext example" <<
                      "gentoo" <<
                      "gentoo linux" <<
                      "gentoo xcfe" <<
                      "gentoo gnome" <<
                      "gentoo kde" <<
                      "grub" <<
                      "tits");
    TrieSpeller speller;
    speller.loadDictionaryFromFile(dictionary.fileName());
    node_list nodes = speller.tree->searchPattern("ge");
    QCOMPARE(nodes.count(), 1);

    node_list completions, matches;
    speller.CompleteWords(nodes, completions, matches);

    QCOMPARE(completions.count(), 4);
    QCOMPARE(completions[0]->fullPath(), QString("gettext$"));
    QCOMPARE(completions[1]->fullPath(), QString("gettext "));
    QCOMPARE(completions[2]->fullPath(), QString("gentoo$"));
    QCOMPARE(completions[3]->fullPath(), QString("gentoo "));

    QCOMPARE(matches.count(), 4);
    QCOMPARE(matches[0]->fullPath(), QString("ge"));
    QVERIFY(matches[0] == matches[1]);
    QVERIFY(matches[0] == matches[2]);
    QVERIFY(matches[0] == matches[3]);
}


/** Проверка сортировки результатов по темам */
void TestSuggestLib::test_ThemeGrouping()
{
    CompiledDictionary dictionary(QStringList() <<
                      /******************************************
                        term                  theme       rate
                       *****************************************/
                      "gettext"         "\t" "c"     "\t" "20" <<
                      "gettext source"  "\t" "c"     "\t" "10" <<
                      "gettext example" "\t" "c"     "\t" "40" <<
                      "gentoo"          "\t" "linux" "\t" "30" <<
                      "gentoo linux"    "\t" "linux" "\t" "50" <<
                      "gentoo xcfe"     "\t" "linux" "\t" "10" <<
                      "gentoo gnome"    "\t" "linux" "\t" "10" <<
                      "gentoo kde"      "\t" "linux" "\t" "10" <<
                      "grub"            "\t" "linux" "\t" "200" <<
                      "tits"            "\t" "other" "\t" "10");
    TrieSpeller speller;
    speller.loadDictionaryFromFile(dictionary.fileName());
    node_list nodes;
    node_list matches;
    QString query = "g";
    bool is_misspelled;
    speller.SuggestAll(query, nodes, is_misspelled, matches);
    TrieSpellerResults results =
            speller.GroupNodesByThemes(nodes, 10, query,
                                       /*phoneticSort=*/ false,
                                       matches);

    TrieSpellerResults::list_results
            results_c = results.results_by_theme_title("c"),
            results_linux = results.results_by_theme_title("linux");

    CheckResults(results_c, QStringList() <<
                 "gettext \t 50" <<
                 "gettext$\t 20");
    CheckResults(results_linux, QStringList() <<
                 "grub$\t   200" <<
                 "gentoo \t 80" <<
                 "gentoo$\t 30");
    CheckAllMatches(results_c, "g");
    CheckAllMatches(results_linux, "g");
}


/** Проверка разворачивания подсказок до следующих слов. */
void TestSuggestLib::test_ExpandSuggestions()
{
    CompiledDictionary dictionary(QStringList() <<
                      /******************************************
                        term                  theme       rate
                       *****************************************/
                      "gettext"         "\t" "c"     "\t" "20" <<
                      "gettext source"  "\t" "c"     "\t" "10" <<
                      "gettext example" "\t" "c"     "\t" "40" <<
                      "gettime"         "\t" "c"     "\t" "25" <<
                      "gettime source"  "\t" "c"     "\t" "15" <<
                      "gettime example" "\t" "c"     "\t" "45" <<
                      "gentoo"          "\t" "linux" "\t" "30" <<
                      "gentoo linux"    "\t" "linux" "\t" "50" <<
                      "gentoo xcfe"     "\t" "linux" "\t" "10" <<
                      "gentoo gnome"    "\t" "linux" "\t" "10" <<
                      "gentoo kde"      "\t" "linux" "\t" "10" <<
                      "grub"            "\t" "linux" "\t" "200" <<
                      "tits"            "\t" "other" "\t" "10");

    // Получаем подсказки
    TrieSpeller speller;
    speller.loadDictionaryFromFile(dictionary.fileName());
    node_list nodes;
    node_list matches;
    QString query = "g";
    bool is_misspelled;
    speller.SuggestAll(query, nodes, is_misspelled, matches);
    TrieSpellerResults results =
            speller.GroupNodesByThemes(nodes, 10, query,/*phoneticSort=*/false, matches);
    CheckResults(results.results_by_theme_title("c"), QStringList() <<
                 "gettime \t 60" <<
                 "gettext \t 50" <<
                 "gettime$\t 25" <<
                 "gettext$\t 20");

    // Расширяем подсказки
    speller.ExpandSuggestions(results, 5);

    // Проверяем результаты
    /* TODO: Вообще-то рейтинг развёрнутой подсказки должен вычитаться из
             разворачиваемой. Например, если из "gettime " с рейтингом 60
             мы выделяем "gettime example$" с рейтингом 45, рейтинг "gettime "
             должен стать 15 и эта подсказка должна опуститься ниже в списке
             результатов. Поэтому, должен проходить закомментированный тест. */
//    CheckResults(results.results_by_theme_title("c"), QStringList() <<
//                 "gettime example$\t 45" <<
//                 "gettext \t 50" <<
//                 "gettime$\t 25" <<
//                 "gettext$\t 20" <<
//                 "gettime \t 15");

    CheckResults(results.results_by_theme_title("c"), QStringList() <<
                 "gettime \t 60" <<
                 "gettext \t 50" <<
                 "gettime$\t 25" <<
                 "gettext$\t 20" <<
                 "gettime example$\t 45");

    CheckResults(results.results_by_theme_title("linux"), QStringList() <<
                 "grub$\t         200" <<
                 "gentoo \t       80" <<
                 "gentoo$\t       30" <<
                 "gentoo linux$\t 50" <<
                 "gentoo xcfe$\t  10");
}

/** Подсказку, которую полностью развернули, нужно убрать из
    результатов */
void TestSuggestLib::test_RemoveFullyExpandedSuggestion()
{
    CompiledDictionary dictionary(QStringList() <<
                      /******************************************
                        term                  theme       rate
                       *****************************************/
                      "gentoo"          "\t" "linux" "\t" "30" <<
                      "gentoo linux"    "\t" "linux" "\t" "50" <<
                      "gentoo xcfe"     "\t" "linux" "\t" "10" <<
                      "gentoo gnome"    "\t" "linux" "\t" "10" <<
                      "gentoo kde"      "\t" "linux" "\t" "10" <<
                      "grub"            "\t" "linux" "\t" "200");
    TrieSpeller speller;
    speller.loadDictionaryFromFile(dictionary.fileName());
    node_list nodes;
    node_list matches;
    QString query = "g";
    bool is_misspelled;
    speller.SuggestAll(query, nodes, is_misspelled, matches);
    TrieSpellerResults results =
            speller.GroupNodesByThemes(nodes, 10, query,
                                       /*phoneticSort=*/false,
                                       matches);
    speller.ExpandSuggestions(results, 10);
    // В результатах не должно быть "gentoo "
    CheckResults(results.results_by_theme_title("linux"), QStringList() <<
                 "grub$" <<
                 "gentoo$" <<
                 "gentoo linux$" <<
                 "gentoo xcfe$" <<
                 "gentoo gnome$" <<
                 "gentoo kde$");
}

/** Подсказки, по которым остался единственный вариант продолжения
    нужно разворачивать до самого конца */
void TestSuggestLib::test_ExpandSuggestionsToEnd()
{
    CompiledDictionary dictionary(QStringList() <<
                      /******************************************
                        term                  theme       rate
                       *****************************************/
                      "gentoo"          "\t" "linux" "\t" "50" <<
                      "gentoo linux"    "\t" "linux" "\t" "30" <<
                      "gentoo kde very long query"  "\t" "linux" "\t" "10" <<
                      "grub"            "\t" "linux" "\t" "200");
    TrieSpeller speller;
    speller.loadDictionaryFromFile(dictionary.fileName());
    node_list nodes;
    node_list matches;
    QString query;
    bool is_misspelled;
    speller.SuggestAll(query, nodes, is_misspelled, matches);
    TrieSpellerResults results =
            speller.GroupNodesByThemes(nodes, 10, query,
                                       /*phoneticSort=*/false,
                                       matches);
    speller.ExpandSuggestions(results, 10);
    // Все "gentoo kde" должны развернуться
    CheckResults(results.results_by_theme_title("linux"), QStringList() <<
                 "grub$" <<
                 "gentoo$" <<
                 "gentoo linux$" <<
                 "gentoo kde very long query$");
}


/** Проверка подсказок в случае, когда введено всё слово */
void TestSuggestLib::test_SuggestWholeWord()
{
    CompiledDictionary dictionary(QStringList() <<
                                  "download"           "\t1\t1" <<
                                  "download free"      "\t1\t1" <<
                                  "download firefox"   "\t1\t1");
    TrieSpeller speller;
    speller.loadDictionaryFromFile(dictionary.fileName());
    {
        node_list nodes;
        node_list matches;
        bool is_misspelled;
        speller.SuggestAll("download", nodes, is_misspelled, matches);
        QCOMPARE(nodes.size(), 2);          // "download " и "download$"
    }
    {
        TrieSpellerResults results = speller.suggest("download");
        QCOMPARE(results.results_by_theme_title("1").size(), 3);
    }

}


/** Проверка поддержки неразрывных пробелов. */
void TestSuggestLib::test_NonbreakingSpace()
{
    CompiledDictionary dictionary(QStringList() <<
                                  "vodka_kozatska_rada"
                                  );
    TrieSpeller speller;
    speller.config.fixSpelling = false;
    speller.config.fixSpellingLight = false;
    speller.config.phoneticSort = false;
    speller.config.fixLayout = false;
    speller.loadDictionaryFromFile(dictionary.fileName());

    {
        node_list nodes, matches;
        bool is_misspelled;
        speller.SuggestAll("vodka kozatska ", nodes, is_misspelled, matches);

        QVERIFY(!is_misspelled);
        QCOMPARE(nodes.size(), 1);
    }


}


/** Проверка выдачи подсказок по неправильному запросе при "лёгком"
    способе исправления орфографии */
void TestSuggestLib::test_MisspeledSuggestSimpleSpeller()
{
    CompiledDictionary dictionary(QStringList() <<
                                  "скачать"           "\t1\t1" <<
                                  "скачать бесплатно" "\t1\t1" <<
                                  "скачать без платы" "\t1\t1" <<
                                  "скучать по тебе"   "\t1\t1" <<
                                  "скачки лошадей"    "\t1\t1" <<
                                  "бездонное небо"    "\t1\t1" <<
                                  "осенняя листва"    "\t1\t1");
    TrieSpeller speller;
    speller.loadDictionaryFromFile(dictionary.fileName());
    {
        speller.config.fixSpelling = false;
        speller.config.fixSpellingLight = true;

        // Исправление "о"-"а"
        {
            node_list nodes;
            speller.SearchMisspeled("скочать", nodes);
            QCOMPARE(nodes.size(), 1);
        }
        {
            TrieSpellerResults results = speller.suggest("скочат");
            QCOMPARE(results.results_by_theme_title("1").length(), 3);
        }
        // Исправление "с"-"з"
        {
            TrieSpellerResults results = speller.suggest("зкачать");
            QCOMPARE(results.results_by_theme_title("1").length(), 3);
        }
        // Исправление "нн"
        {
            TrieSpellerResults results = speller.suggest("бездоное");
            QCOMPARE(results.results_by_theme_title("1").length(), 1);
        }
        // Комплексные тесты
        {
            TrieSpellerResults results = speller.suggest("зкочать бес платы");
            QCOMPARE(results.results_by_theme_title("1").length(), 1);
            results = speller.suggest("асеняя лества");
            QCOMPARE(results.results_by_theme_title("1").length(), 1);
            results = speller.suggest("бесдоное неба");
            QCOMPARE(results.results_by_theme_title("1").length(), 1);
        }
    }
}


/** Проверка выдачи подсказок по неправильному запросе в "полном" режиме
    исправления орфографии */
void TestSuggestLib::test_MisspeledSuggestFullSpeller()
{
    CompiledDictionary dictionary(QStringList() <<
                                  "скачать"           "\t1\t1" <<
                                  "скачать бесплатно" "\t1\t1" <<
                                  "скачать без платы" "\t1\t1" <<
                                  "скучать по тебе"   "\t1\t1" <<
                                  "скачки лошадей"    "\t1\t1");
    {
        TrieSpeller speller;
        speller.loadDictionaryFromFile(dictionary.fileName());
        speller.config.fixSpelling = true;
        speller.config.fixSpellingLight = false;

        // Пропущенная буква
        {
            TrieSpellerResults results = speller.suggest("скчать");
            QCOMPARE(results.results_by_theme_title("1").length(), 4);
            CheckResults(results.results_by_theme_title("1"), QStringList() <<
                         "скачать$" <<
                         "скачать бесплатно$" <<
                         "скачать без платы$" <<
                         "скучать по тебе$");
        }
        // Неправильно набранная буква
        {
            TrieSpellerResults results = speller.suggest("скаXать");
            QCOMPARE(results.results_by_theme_title("1").length(), 3);
            CheckResults(results.results_by_theme_title("1"), QStringList() <<
                         "скачать$" <<
                         "скачать бесплатно$" <<
                         "скачать без платы$");
        }
        // Вставленная буква
        {
            TrieSpellerResults results = speller.suggest("скачаXть");
            QCOMPARE(results.results_by_theme_title("1").length(), 3);
            CheckResults(results.results_by_theme_title("1"), QStringList() <<
                         "скачать$" <<
                         "скачать бесплатно$" <<
                         "скачать без платы$");
        }
        // Перестановка букв местами
        {
            TrieSpellerResults results = speller.suggest("ксачать");
            QCOMPARE(results.results_by_theme_title("1").length(), 3);
            CheckResults(results.results_by_theme_title("1"), QStringList() <<
                         "скачать$" <<
                         "скачать бесплатно$" <<
                         "скачать без платы$");
        }
    }
    {   // Проверка комбинированных методов исправления: "лёгкого" и полного
        TrieSpeller speller;
        speller.loadDictionaryFromFile(dictionary.fileName());
        speller.config.fixSpelling = true;
        speller.config.fixSpellingLight = true;

        // Пропущенная буква
        {
            TrieSpellerResults results = speller.suggest("зкXчать");
            QCOMPARE(results.results_by_theme_title("1").length(), 4);
            CheckResults(results.results_by_theme_title("1"), QStringList() <<
                         "скачать$" <<
                         "скачать бесплатно$" <<
                         "скачать без платы$" <<
                         "скучать по тебе$");
        }
    }
}


/** Тесты поддержки кириллицы */
void TestSuggestLib::test_CyrilicQueries()
{
    CompiledDictionary dictionary(QStringList() <<
                                  "скачать"            "\t1\t1" <<
                                  "скачать бесплатно"  "\t1\t1" <<
                                  "скачать без платы"  "\t1\t1" <<
                                  "скучать по тебе"    "\t1\t1" <<
                                  "скачки лошадей"     "\t1\t1" <<
                                  "english"            "\t1\t1" <<
                                  "elbow"              "\t1\t1");
    TrieSpeller speller;
    speller.loadDictionaryFromFile(dictionary.fileName());
    {
        TrieSpellerResults results = speller.suggest("ск");
        QCOMPARE(results.results_by_theme_title("1").count(), 5);
    }
}

/** Проверка извлечения данных о рейтингах тематик из узлов */
void TestSuggestLib::test_CountersData()
{
    TrieSpeller speller;
    QCOMPARE(speller.ParseCountersData("T1:10:15", "T1"), 10);
    QCOMPARE(speller.ParseCountersData("T1:10:15;T2:11:16", "T2"), 11);
    QCOMPARE(speller.ParseCountersData("T1:10:15;T2:11:16", "!!!"), 0);
    QCOMPARE(speller.ParseRateData("T1:10:15", "T1"), 15);
    QCOMPARE(speller.ParseRateData("T1:10:15;T2:11:16", "T2"), 16);
    QCOMPARE(speller.ParseRateData("T1:10:15;T2:11:16", "!!!"), 0);
}


/** Тест на запросы, которые начинаются с узла типа Chain. */
void TestSuggestLib::test_QueryInFirstChainNode()
{
    CompiledDictionary dictionary(QStringList() <<
                                  "эллипсоид tunturi сf35"    "\t1\t1",
                                  false /* TODO: temp */);
    TrieSpeller speller;
    speller.loadDictionaryFromFile(dictionary.fileName());
    {
        TrieSpellerResults results = speller.suggest("элли");
        QCOMPARE(results.results_by_theme_title("1").count(), 1);
    }
}


/** Проверка, что из подсказок, полученных исправлением орфографии,
    убираются дубликаты. */
void TestSuggestLib::test_RemoveDuplicatedSuggestions()
{
   CompiledDictionary dictionary(QStringList() <<
                                 "одноклассники$"    "\t1\t1");
    TrieSpeller speller;
    speller.loadDictionaryFromFile(dictionary.fileName());
    speller.config.fixSpelling = true;
    speller.config.fixSpellingLight = true;
    TrieSpellerResults all_results = speller.suggest("адна");
    TrieSpellerResults::list_results results =
            all_results.results_by_theme_title("1");

    QCOMPARE(results.count(), 1);
}


/** Проверка удаления повторяющихся узлов. */
void TestSuggestLib::test_RemoveDuplicateNodes()
{
    TrieSpeller speller;
    CompiledDictionary dictionary(QStringList() <<
                                  "ab" <<
                                  "ac" <<
                                  "z");
    speller.loadDictionaryFromFile(dictionary.fileName());
    speller.config.fixSpelling = false;

    // Получаем узлы 'ab', 'ac' и 'a'.
    node_list nodes;
    speller.SearchMisspeled("ab", nodes);
    TrieCompiledNode *node_ab = nodes[0];

    nodes.clear();
    speller.SearchMisspeled("ac", nodes);
    TrieCompiledNode *node_ac = nodes[0];

    nodes.clear();
    speller.SearchMisspeled("a", nodes);
    TrieCompiledNode *node_a = nodes[0];

    // Составляем список с повторами
    nodes.clear();
    nodes.append(node_ab);
    nodes.append(node_ac);
    nodes.append(node_ab);
    nodes.append(node_ac);
    nodes.append(node_ac);

    node_list matches;
    matches.append(node_a);
    matches.append(node_a);
    matches.append(node_a);
    matches.append(node_a);
    matches.append(node_a);

    // Выполняем тест
    speller.removeDuplicateNodes(nodes, &matches);

    QCOMPARE(nodes.count(), 2);
    QVERIFY(nodes[0] == node_ab);
    QVERIFY(nodes[1] == node_ac);

    QCOMPARE(matches.count(), 2);
    QVERIFY(matches[0] == node_a);
    QVERIFY(matches[1] == node_a);
}


/** Проверка на то, что результаты сортируются по фонетической близости. */
void TestSuggestLib::test_SuggestionSortings()
{
    // Все подсказки в этом словаре могут быть получены исправлением слова
    // "барада". Обратите внимание, что вес слова "борода" ниже, чем у всех
    // остальных слов. Несмотря на это, на первом месте мы должны получить
    // именно "борода"
    CompiledDictionary dictionary(QStringList() <<
                                  "борода1"  "\t1"   "\t50"  <<
                                  "города2"  "\t1"   "\t100" <<
                                  "народом3" "\t1"   "\t100" <<
                                  "порода4"  "\t1"   "\t100" <<
                                  "барабан5" "\t1"   "\t100" <<
                                  "бородин6" "\t1"   "\t100"
                                  );
    TrieSpeller speller;
    speller.loadDictionaryFromFile(dictionary.fileName());
    speller.config.fixSpelling = true;
    speller.config.fixSpellingLight = true;
    speller.config.phoneticSort = true;

    TrieSpellerResults results = speller.suggest("барада");

    TrieSpellerResults::list_results listResults =
            results.results_by_theme_title("1");

    QCOMPARE(listResults.count(), 6);

    QString firstSuggestion = listResults[0].node->fullPath();
    QString expected = "борода1$";
    QCOMPARE(firstSuggestion, expected);

}


/** Тест вычисления расстояния правки. */
void TestSuggestLib::test_EditDistance()
{
    QCOMPARE(LingvoTools::distance("hello", "hello"), 0);
    QCOMPARE(LingvoTools::distance("hello", "helo"), 1);
    QCOMPARE(LingvoTools::distance("hello", "hella"), 1);
    QCOMPARE(LingvoTools::distance("hello", "ehllo"), 1);
    QCOMPARE(LingvoTools::distance("hello", "heello"), 1);
}


/** Тест вычисления фонетической близости. */
void TestSuggestLib::test_PhoneticDistance()
{
    // Совместимость с расстоянием Левенштейна
    QCOMPARE(LingvoTools::distancePhonetic("hello", "hello"), 0);
    QCOMPARE(LingvoTools::distancePhonetic("hello", "helo"), 10);
    QCOMPARE(LingvoTools::distancePhonetic("hello", "hellp"), 10);
    QCOMPARE(LingvoTools::distancePhonetic("hello", "ehllo"), 10 + LingvoTools::COST_WORD_BEGINNING_PENALITY);
    QCOMPARE(LingvoTools::distancePhonetic("hello", "heello"), 10);

    // Лёгкая опечатка
    QCOMPARE(LingvoTools::distancePhonetic("борода", "борада"),
             int(LingvoTools::COST_LIGHT_REPLACEMENT));

    // Пенальти за ошибку в начале слова
    QCOMPARE(LingvoTools::distancePhonetic("города", "борода"),
             10 + LingvoTools::COST_WORD_BEGINNING_PENALITY);

    QCOMPARE(LingvoTools::distancePhonetic("борода", "барода"),
             LingvoTools::COST_LIGHT_REPLACEMENT + LingvoTools::COST_WORD_BEGINNING_PENALITY);
}


/** Проверка обработки matches на разных этапах получения подсказок. */
void TestSuggestLib::test_Matches()
{
    CompiledDictionary dictionary(QStringList() <<
                                  "download"           "\t1\t1" <<
                                  "download free"      "\t1\t1" <<
                                  "download firefox"   "\t1\t1" <<
                                  "something else"     "\t1\t1");

    TrieSpeller speller;
    speller.loadDictionaryFromFile(dictionary.fileName());

    QStringList expected = QStringList() << "down"
                                         << "down"
                                         << "down";

    // SuggestAll
    node_list suggestedNodes;
    node_list matches;
    bool is_misspelled;
    speller.SuggestAll("down", suggestedNodes, is_misspelled, matches);
    QCOMPARE(suggestedNodes.size(), 2);
    CheckNodeList(matches, QStringList() << "down" << "down");

    // removeDuplicateNodes
    speller.removeDuplicateNodes(suggestedNodes, &matches);
    QCOMPARE(suggestedNodes.size(), 2);
    CheckNodeList(matches, QStringList() << "down" << "down");

    // GroupNodesByThemes
    bool phoneticSort = false;
    TrieSpellerResults results =
            speller.GroupNodesByThemes(suggestedNodes, /*top=*/10, "down",
                                       phoneticSort, matches);
    QCOMPARE(results.results_by_theme_title("1").size(), 2);
    CheckAllMatches(results.results_by_theme_title("1"), "down");

    // ExpandSuggestions
    speller.ExpandSuggestions(results, /*top=*/10);
    QCOMPARE(results.results_by_theme_title("1").size(), 3);
    CheckAllMatches(results.results_by_theme_title("1"), "down");
}


/** Тест выделения набранного в результатах для простого случая. */
void TestSuggestLib::test_HighlightSimpleCase()
{
    CompiledDictionary dictionary(QStringList() <<
                                  "download"           "\t1\t1" <<
                                  "download free"      "\t1\t1" <<
                                  "download firefox"   "\t1\t1" <<
                                  "damn small linux"   "\t1\t1" <<
                                  "something else"     "\t1\t1");

    TrieSpeller speller;
    speller.loadDictionaryFromFile(dictionary.fileName());

    TrieSpellerResults all_results = speller.suggest("down");
    TrieSpellerResults::list_results results =
            all_results.results_by_theme_title("1");
    QCOMPARE(results.length(), 3);
    CheckAllMatches(results, "down");
}

/** Тест выделения набранного в результатах с исправлением орфографии:
  замена неправильно набранного символа с сохранением длины подсказки.
 */
void TestSuggestLib::test_HighlightSpellingCorrectionsCase1()
{
    CompiledDictionary dictionary(QStringList() <<
                                  "download"           "\t1\t1" <<
                                  "download free"      "\t1\t1" <<
                                  "download firefox"   "\t1\t1" <<
                                  "damn small linux"   "\t1\t1" <<
                                  "something else"     "\t1\t1");

    TrieSpeller speller;
    speller.loadDictionaryFromFile(dictionary.fileName());
    speller.config.fixLayout = true;
    speller.config.fixSpelling = true;
    speller.config.fixSpellingLight = true;

    // Подсказка по "dawn" быть быть с одинаковым успехом исправлена как в
    // "down[load]", так и в "damn [small linux]"
    TrieSpellerResults all_results = speller.suggest("dawn");
    TrieSpellerResults::list_results results =
            all_results.results_by_theme_title("1");

    QCOMPARE(results.length(), 4);
    QStringList expected_matches = QStringList() << "down"
                                                 << "down"
                                                 << "down"
                                                 << "damn";
    CheckMatches(results, expected_matches);
}

/** Тест выделения набранного в результатах с исправлением орфографии:
  удаление неправильно набранного символа с изменением длины подсказки.
 */
void TestSuggestLib::test_HighlightSpellingCorrectionsCase2()
{
//    CompiledDictionary dictionary(QStringList() <<
//                                  "download"           "\t1\t1" <<
//                                  "download free"      "\t1\t1" <<
//                                  "download firefox"   "\t1\t1" <<
//                                  "something else"     "\t1\t1");

//    TrieSpeller speller;
//    speller.loadDictionaryFromFile(dictionary.fileName());
//    speller.config.fixLayout = true;
//    speller.config.fixSpelling = true;
//    speller.config.fixSpellingLight = true;

//    TrieSpellerResults all_results = speller.suggest("download1");
//    TrieSpellerResults::list_results results =
//            all_results.results_by_theme_title("1");

//    foreach (TrieSpellerResults::Result r, results) {
//        QWARN(r.node->fullPath().toUtf8().data());
//    }

//    // TODO: Почему-то даёт 5 результатов
//    QCOMPARE(results.length(), 3);
//    QStringList expected_matches = QStringList() << "download"
//                                                 << "download "
//                                                 << "download ";
//    CheckMatches(results, expected_matches);
}

/** Тест выделения набранного в результатах с исправлением раскладки.
 */
void TestSuggestLib::test_HighlightFixedLayout()
{
    CompiledDictionary dictionary(QStringList() <<
                                  "южная америка"      "\t1\t1" <<
                                  "something else"     "\t1\t1");

    TrieSpeller speller;
    speller.loadDictionaryFromFile(dictionary.fileName());
    speller.config.fixLayout = true;
    speller.config.fixSpelling = true;
    speller.config.fixSpellingLight = true;

    TrieSpellerResults all_results = speller.suggest(".;yfz");
    TrieSpellerResults::list_results results =
            all_results.results_by_theme_title("1");

//    foreach (TrieSpellerResults::Result r, results) {
//        QWARN(r.node->fullPath().toUtf8().data());
//    }

    QCOMPARE(results.length(), 2);
//    QStringList expected_matches = QStringList() << "южная" << "южная";
    CheckAllMatches(results, QString("южная"));
}



QTEST_APPLESS_MAIN(TestSuggestLib)
#include "SuggestLibTest.moc"
