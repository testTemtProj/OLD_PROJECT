#-------------------------------------------------
#
# Project created by QtCreator 2011-03-25T11:57:08
#
#-------------------------------------------------

QT       += testlib

QT       -= gui

TARGET = tst_BuilderTest
CONFIG   += console silent
CONFIG   -= app_bundle
TEMPLATE = app
DESTDIR = bin
MOC_DIR = build
OBJECTS_DIR = build


SOURCES += tst_BuilderTest.cpp
DEFINES += SRCDIR=\\\"$$PWD/\\\"

include(../TrieLib/TrieLib.pri)
