#include <QtCore/QString>
#include <QtTest/QtTest>
#include <cstring>
#include <TrieBuilder.h>
#include <TrieCompiled.h>

class BuilderTest : public QObject
{
    Q_OBJECT

public:
    BuilderTest();

private Q_SLOTS:
    void init();
    void testAddNodes();
    void testAddDuplicates();
    void testSaveAndRestoreAndSearch();
    void testCyrillic();
    void testUserData();
    void testMetaData();
    void cleanup();

private:
    TrieBuilder *builder;
    void DumpBinaryData(QIODevice &in);
};

BuilderTest::BuilderTest()
    : builder(0)
{
}

void BuilderTest::init()
{
    builder = new TrieBuilder;
}

void BuilderTest::cleanup()
{
    delete builder;
}

/** Выводит двоичные данные на экран в удобном виде */
void BuilderTest::DumpBinaryData(QIODevice &in)
{
    qDebug() << "-------------- DUMP FOLLOWS: -----------------";
    in.open(QIODevice::ReadOnly);
    QByteArray buffer;
    in.seek(0);
    while ((buffer = in.read(8)).size()) {
        qDebug() << buffer.toHex();
    }
}

/** Тест добавления узлов в TrieBuilder */
void BuilderTest::testAddNodes()
{
    BuilderNode *node_a = builder->addNode('a', builder->root());
    BuilderNode *node_z = builder->addNode('z', builder->root());
    BuilderNode *node_b = builder->addNode('b', node_a);
    BuilderNode *node_c = builder->addNode('c', node_a);
    node_c->setData(QByteArray("###"));

    QCOMPARE(builder->nodeCount(), 4);
    QCOMPARE(node_a->value(), 'a');
    QCOMPARE(node_a->parent(), builder->root());
    QCOMPARE(node_b->value(), 'b');
    QCOMPARE(node_b->parent(), node_a);
    QCOMPARE(node_c->value(), 'c');
    QCOMPARE(node_c->parent(), node_a);
    QVERIFY(builder->root()->children().contains(node_a));
    QVERIFY(builder->root()->children().contains(node_z));
    QVERIFY(node_a->children().contains(node_b));
    QVERIFY(node_a->children().contains(node_c));

    QVERIFY(node_c->data() == QByteArray("###") );
}


/** Тест на добавления дублирующихся узлов */
void BuilderTest::testAddDuplicates()
{
    builder->addNode('a', builder->root());
    builder->addNode('a', builder->root());
    builder->addNode('b', builder->root());
    QCOMPARE(builder->root()->children().count(), 2);
}


/** Тест на сохранение, загрузку и поиск по дереву */
void BuilderTest::testSaveAndRestoreAndSearch()
{
    testAddNodes();

    QTemporaryFile file;
    file.open();
    builder->save(file);
    file.close();

    TrieCompiled trie(file.fileName());
    QCOMPARE(trie.searchPattern("a").count(), 1);
    QCOMPARE(trie.searchPattern("!").count(), 0);
    QCOMPARE(trie.searchPattern("ab").count(), 1);
    QCOMPARE(trie.searchPattern("a.").count(), 2);
    QCOMPARE(trie.searchPattern("[az]b").count(), 1);
    QCOMPARE(trie.searchPattern("[az][x?]b").count(), 1);
}


/** Проверка поддержки кириллицы */
void BuilderTest::testCyrillic()
{
    QTextCodec::setCodecForCStrings(QTextCodec::codecForName("UTF-8"));
    QTextCodec::setCodecForLocale(QTextCodec::codecForName("UTF-8"));
    // д - о - м
    //   \ а
    BuilderNode *node_d = builder->addNode(0xE4, builder->root());      // д
    BuilderNode *node_a = builder->addNode(0xE0, node_d);               // а
    BuilderNode *node_o = builder->addNode(0xEE, node_d);               // о
    BuilderNode *node_m = builder->addNode(0xEC, node_o);               // м

    QTemporaryFile file;
    file.open();
    builder->save(file);
    file.close();

    TrieCompiled trie(file.fileName());
    QCOMPARE(trie.searchPattern("д").count(), 1);
    QCOMPARE(trie.searchPattern("я").count(), 0);
    QCOMPARE(trie.searchPattern("да").count(), 1);
    QCOMPARE(trie.searchPattern("д[ы?]а").count(), 1);
    QCOMPARE(trie.searchPattern(".ом").count(), 1);
    QCOMPARE(trie.searchPattern("д[ао]").count(), 2);

    Q_UNUSED( node_o );
    Q_UNUSED( node_m );
    Q_UNUSED( node_a );
}


/** Проверка сохранения пользовательских данных */
void BuilderTest::testUserData()
{
    BuilderNode *node_a = builder->addNode('a', builder->root());
    BuilderNode *node_b = builder->addNode('b', node_a);
    BuilderNode *node_space = builder->addNode(' ', node_b);
    BuilderNode *node_dollar = builder->addNode('$', node_b);
    BuilderNode *node_c = builder->addNode('c', node_space);
    node_space->setData("space data");
    node_dollar->setData("dollar data");
    QCOMPARE(node_space->data(), QByteArray("space data"));
    QCOMPARE(node_dollar->data(), QByteArray("dollar data"));
    Q_UNUSED(node_c);
}

/** Проверка сохранения мета-данных всего словаря */
void BuilderTest::testMetaData()
{
    testAddNodes();
    builder->setMetaData("Version", "1.0");
    builder->setMetaData("Unicode string", QString("Привет, мир!").toUtf8());

    QTemporaryFile f;
    f.open();
    builder->save(f);
    f.close();

    TrieCompiled trie(f.fileName());
    QCOMPARE(trie.metaData("Version"), QByteArray("1.0"));
    QCOMPARE(trie.metaData("Unicode string"), QString("Привет, мир!").toUtf8());
}

QTEST_APPLESS_MAIN(BuilderTest);

#include "tst_BuilderTest.moc"
