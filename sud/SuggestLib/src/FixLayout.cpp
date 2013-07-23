/*
 * FixLayout.cpp
 *
 *  Created on: 2 лип. 2009
 *      Author: Silver
 *
 * Определение ошибочной раскладки клавиатуры и исправление.
 */

#include <QTextCodec>

#include "FixLayout.h"
#include "FixLayout_triggers.cpp"


FixLayout::FixLayout()
{
    /* Инициализация таблицы замещения */
    QTextCodec *previous_codec = QTextCodec::codecForCStrings();
    QTextCodec::setCodecForCStrings(QTextCodec::codecForName("UTF-8"));

    engLayout = "`qwertyuiop[]asdfghjkl;'zxcvbnm,."
                "~QWERTYUIOP{}ASDFGHJKL:\"ZXCVBNM<>";
    rusLayout = "ёйцукенгшщзхъфывапролджэячсмитьбю"
                "ЁЙЦУКЕНГШЩЗХЪФЫВАПРОЛДЖЭЯЧСМИТЬБЮ";

    QTextCodec::setCodecForCStrings(previous_codec);

    Q_ASSERT( engLayout.length() == rusLayout.length() );

    for (int i = 0; i < engLayout.length(); i++) {
        convert[engLayout[i]] = rusLayout[i];
        convert[rusLayout[i]] = engLayout[i];
    }
}

FixLayout::~FixLayout() { }



/*
 * Переводит слово в противоположную раскладку (русская <-> английская)
 */
QString FixLayout::convertLayout(const QString &s)
{
    QString res;

    for (int i = 0; i < s.length(); i++) {
        if (convert.contains(s[i])) {
            res += convert[s[i]];
        }
        else
            res += s[i];
    }

    return res;
}
