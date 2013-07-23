#-------------------------------------------------
#
# Project created by QtCreator 2011-03-25T11:54:29
#
#-------------------------------------------------

#QT       -= gui

#TARGET = TrieLib
#TEMPLATE = lib
#CONFIG += staticlib silent
INCLUDEPATH += $$PWD
DEPENDPATH += $$PWD

SOURCES += TrieLib.cpp \
    ../TrieLib/TrieBuilder.cpp \
    ../TrieLib/TrieBuilder_impl.cpp \
    ../TrieLib/TrieCompiled.cpp \
    ../TrieLib/TrieCompiledNode.cpp

HEADERS += TrieLib.h \
    ../TrieLib/TrieBuilder.h \
    ../TrieLib/TrieCompiled.h \
    ../TrieLib/TrieCompiledNode.h
