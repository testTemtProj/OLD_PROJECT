#ifndef TRIEBUILDER_H
#define TRIEBUILDER_H

#include <QString>
#include <QList>
#include <QIODevice>
#include <memory>

class TrieBuilderImpl;
class BuilderNode;

typedef char char_t;

// -----------------------------------------------------------
class TrieBuilder
{
public:
    TrieBuilder();

    /** Добавляет узел \a value в дерево */
    BuilderNode *addNode(char_t value, BuilderNode *parent);

    /** Корневой узел дерева */
    BuilderNode *root() const;

    /** Количество узлов в дереве */
    int nodeCount() const;

    /** Сохраняет компилированное дерево в \a out */
    void save(QIODevice &out);

    /** Присваивает дереву мета-данные \a data с ключём \a key.
        Если \a data -- это строка QString, то она будет сохранена в UTF-8. */
    void setMetaData(const QString &key, const QByteArray &data);
    void setMetaData(const QString &key, const QString &data);

    /** Возвращает присвоенные дереву мета-данные по ключу \a key */
    QByteArray metaData(const QString &key) const;

private:
    std::auto_ptr<TrieBuilderImpl> p;
};


// -----------------------------------------------------------
class BuilderNode
{
public:
    BuilderNode(char_t value, BuilderNode *parent);
    ~BuilderNode();

    enum NodeType {
            Terminator = 0,
            OneChar = 1,
            Chain = 2
    } type;

    enum NodeFlags {
            HasData = 16,
            ShortOffset = 32,
            ChainTerminated = 64,
            ChainSameData = 128
    };

    enum NodeDataRole {
            RateData,
            CountData
    };


    /** Значение, которое хранит узел */
    char_t value() const { return m_value; }

    /** Родительский узел */
    BuilderNode *parent() const { return m_parent; }

    /** Список дочерних узлов */
    QList<BuilderNode*> children() { return m_children; }

    /** Возвращает \a i -го потомка */
    BuilderNode *child(int i) const { return m_children[i]; }

    /** Присваивает узлу данные \a data */
    void setData(const QByteArray &data);

    /** Возвращает данные, ассоциированные с узлом. */
    QByteArray data() const { return m_data; }

private:
    char_t m_value;
    BuilderNode *m_parent;
    QList<BuilderNode*> m_children;
    QByteArray m_data;

    friend class TrieBuilderImpl;
};

#endif // TRIEBUILDER_H
