#include "TrieBuilder.h"
#include "TrieBuilder_impl.cpp"


TrieBuilder::TrieBuilder()
    : p(new TrieBuilderImpl())
{
}

BuilderNode *TrieBuilder::addNode(char_t value, BuilderNode *parent)
{
    return p->addNode(value, parent);
}


BuilderNode *TrieBuilder::root() const
{
    return p->root();
}


int TrieBuilder::nodeCount() const
{
    return p->nodeCount();
}


void TrieBuilder::save(QIODevice &out)
{
    p->save(out);
}

void TrieBuilder::setMetaData(const QString &key, const QByteArray &data)
{
    p->setMetaData(key, data);
}

void TrieBuilder::setMetaData(const QString &key, const QString &data)
{
    p->setMetaData(key, data);
}

QByteArray TrieBuilder::metaData(const QString &key) const
{
    return p->metaData(key);
}


// =============================================================================

BuilderNode::BuilderNode(char_t value, BuilderNode *parent)
    : m_value(value), m_parent(parent)
{
}

BuilderNode::~BuilderNode()
{
}

void BuilderNode::setData(const QByteArray &data)
{
    m_data = data;
}
