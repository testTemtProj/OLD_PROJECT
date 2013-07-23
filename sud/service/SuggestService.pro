TEMPLATE = app
QT += core \
    xml
QT -= gui
TARGET =
DEPENDPATH += . \
    include
INCLUDEPATH += . \
    include
LIBS += -lfcgi -lglog
CONFIG += qt \
    console \
    silent
DESTDIR = bin
MOC_DIR = build
OBJECTS_DIR = build

# Input
SOURCES += \
    src/SuggestService.cpp \
    src/main.cpp

HEADERS += \
    src/pch.h \
    src/SuggestService.h


include(../SuggestLib/SuggestLib.pri)
