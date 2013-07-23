#!/bin/sh
# Скрипт компилирует русскую базу запросов Пастухова в словарь подсказок для веб-поиска
# Первым параметром ожидается путь к файлу базы Пастухова
# Второй параметр -- выходной (скомпилированный) файл
# Третьим параметром может идти путь к файлу с дополнительными подсказами.
# Дополнительные подсказки идут по одной на строку и добавляются в словарь с высоким рейтингом

# Путь к компилятору словарей
COMPILER='../compiler/bin/compiler'

# Путь к временной папке
# Временная папка должна иметь порядка 2 Гб свободного места
TMP_DIR='/tmp'

# Количество подсказок, взятых из базы (отсортированных по рейтингу)
TOP=1000000

CLEANED_FILE=$TMP_DIR/utf8_cleaned.tmp
SORTED_FILE=$TMP_DIR/sorted.tmp
CUSTOM_SUGGEST_FILE=$TMP_DIR/custom.tmp

if [ ! -f $COMPILER ]
  then
     echo Dictionary compiler not found at $COMPILER!
     exit
fi

if [ $# -lt 2 ]
  then
     echo Usage: compile_webru_dictionary.sh PATH_TO_PASTUHOV_KEYWORDS_FILE OUT_FILE [CUSTOM_SUGGEST_FILE]
     exit
fi

if [ ! -f $1 ]
  then
    echo Pastuhov\'s russian keywords file not found!
    exit
fi

if [ ! -f filter.txt ]
  then
    echo Couldn\'t find filter.txt file!
    exit
fi

PASTUHOV=$1
OUT_FILE=$2

# Преобразуем базу Пастухова в UTF-8 и оставляем нужные поля
echo converting to utf8...
pv $PASTUHOV | recode cp1251..utf8 | awk -F \\t '$2 != "NA" {print $1 "\t" "webru" "\t" $2}' > $CLEANED_FILE

# Сортируем по рейтингу и оставляем первые $TOP подсказок
echo sorting...
pv $CLEANED_FILE | sort -k 3 -t "`/bin/echo -e '\t'`" -n --reverse --temporary-directory=$TMP_DIR | head --lines=$TOP > $SORTED_FILE
rm $CLEANED_FILE

INPUT_FILES=$SORTED_FILE

# Подготавливаем дополнительные подсказки (если заданы)
if [ $# -ge 3 ]
  then
    if [ -f $3 ]
      then
        cat $3 | awk -F \\t '{print $1 "\t" "webru" "\t" 999}' > $CUSTOM_SUGGEST_FILE
	INPUT_FILES=$INPUT_FILES" "$CUSTOM_SUGGEST_FILE
    fi
fi 

# Фильтруем от мата, добавляем дополнительные определения и компилируем словарь
echo filtering and compiling...
pv $INPUT_FILES \
    | grep -Ev `echo -n \`cat filter.txt\` | tr ' ' '|'` \
    | $COMPILER $OUT_FILE
rm $SORTED_FILE
