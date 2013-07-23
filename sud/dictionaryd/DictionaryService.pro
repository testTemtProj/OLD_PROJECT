TARGET = DictionaryService
TEMPLATE = app
CONFIG += console qt silent
QT = core \
    xml
SOURCES += src/main.cpp \
    src/DictionaryService.cpp \
    src/DictionaryManager.cpp
HEADERS += src/Exception.h \
    src/DictionaryService.h \
    src/DictionaryManager.h
DESTDIR = bin
MOC_DIR = build
OBJECTS_DIR = build

include(3rdparty/qtservice/src/qtservice.pri)
