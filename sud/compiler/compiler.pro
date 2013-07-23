TEMPLATE = app
QT += core \
    xml
QT -= gui
TARGET = 
LIBS += -lglog
CONFIG += qt \
    console \
    silent
DESTDIR = bin
MOC_DIR = build
OBJECTS_DIR = build
INCLUDE_DIR = src

# Input
SOURCES += \
    src/main.cpp \
    src/DictionaryCompiler.cpp

HEADERS += \
    src/DictionaryCompiler.h

include(../TrieLib/TrieLib.pri)
