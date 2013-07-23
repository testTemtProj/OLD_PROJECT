/*
 * FixLayout.h
 *
 *  Created on: 2 лип. 2009
 *      Author: Silver
 *
 *      Исправляет раскладку клавиатуры (Ghbdtn <=> Привет)
 */

#ifndef FIXLAYOUT_H_
#define FIXLAYOUT_H_

#include <QString>
#include <QtCore>


class FixLayout {
public:
    FixLayout();
    virtual ~FixLayout();

    QString convertLayout(const QString &s);

private:
    bool checkTriggers(const QString &s);

    QString engLayout;
    QString rusLayout;
    QMap <QChar, QChar> convert;
    QMap <QString, QChar> translit;

//    QStringList triggers;

};

#endif /* FIXLAYOUT_H_ */
