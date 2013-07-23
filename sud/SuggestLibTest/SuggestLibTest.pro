#-------------------------------------------------
#
# Project created by QtCreator 2011-03-25T11:57:08
#
#-------------------------------------------------

QT       += testlib

QT       -= gui

TARGET = SuggestLibTest
CONFIG   += console silent
CONFIG   -= app_bundle
TEMPLATE = app
DESTDIR = bin
MOC_DIR = build
OBJECTS_DIR = build
SOURCES += tests/SuggestLibTest.cpp
#DEFINES += SRCDIR=\\\"$$PWD/\\\"

include(../SuggestLib/SuggestLib.pri)
