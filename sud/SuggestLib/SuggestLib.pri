INCLUDEPATH += $$PWD/src
DEPENDPATH += $$PWD

SOURCES += src/TrieSpeller.cpp \
    src/FixLayout.cpp \
    src/LingvoTools.cpp

HEADERS += src/TrieSpeller.h \
    src/FixLayout.h \
    src/LingvoTools.h

include(../TrieLib/TrieLib.pri)
