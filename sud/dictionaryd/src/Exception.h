#ifndef EXCEPTION_H
#define EXCEPTION_H

#include <QString>

class Exception
{
public:
    Exception(const QString &text) : m_text(text) {};
    QString text() const {return m_text; }

private:
    QString m_text;
};


#endif // EXCEPTION_H
