#!/bin/sh
# Скрипт компилирует англоязычную базу запросов Пастухова в словарь подсказок для веб-поиска
# Первым параметром ожидается путь к файлу базы Пастухова
# Второй параметр -- выходной (скомпилированный) файл

# Путь к компилятору словарей
COMPILER='../compiler/bin/compiler'

# Путь к временной папке
# Временная папка должна иметь порядка 2 Гб свободного места
TMP_DIR='/tmp'

# Количество подсказок, взятых из базы (отсортированных по рейтингу)
TOP=1000000

CLEANED_FILE=$TMP_DIR/utf8_cleaned.tmp
SORTED_FILE=$TMP_DIR/sorted.tmp

if [ ! -f $COMPILER ]
  then
     echo Dictionary compiler not found at $COMPILER!
     exit
fi

if [ $# -lt 2 ]
  then
     echo Usage: compile_weben_dictionary.sh PATH_TO_PASTUHOV_KEYWORDS_FILE OUT_FILE
     exit
fi

if [ ! -f $1 ]
  then
    echo Pastuhov\'s english keywords file not found!
    exit
fi

PASTUHOV=$1
OUT_FILE=$2

pv $PASTUHOV \
    | sort -k 3 -t "`/bin/echo -e '\t'`" -n --reverse --temporary-directory=$TMP_DIR \
    | head --lines=$TOP \
    | awk -F \\t '$2 != "NA" {print $1 "\t" "weben" "\t" $2}' \
    | $COMPILER $OUT_FILE
