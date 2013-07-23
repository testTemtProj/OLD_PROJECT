#!/usr/bin/python
# encoding: utf-8
# Скрипт компилирует словарь подсказок для старого Рынка
# Первым параметром ожидает имя выходного файла

# Путь к компилятору словарей
COMPILER = '../compiler/bin/compiler'


try:
    import pymssql
except ImportError:
    print "This script requires pymssql module to be installed!"
    exit(1)

from sys import argv
from subprocess import Popen, PIPE


if len(argv) < 2:
    print "Usage: python compile_rynok_dictionary.py OUT_FILE"
    exit()


print "connecting to database..."
conn = pymssql.connect(host='yottos.com',
                       user='web',                                      
                       password='odif8duuisdofj',                       
                       database='1gb_YottosRynok',                     
                       as_dict=True,                                    
                       charset='cp1251')
c = conn.cursor()
c.execute(
""" select Lot.Title, ClickCost, LotByCategory.RootID, Category.Title Theme 
    from lot inner join LotByCategory on LotByCategory.LotID = Lot.LotID_int 
    inner join Category on Category.CategoryID_int = LotByCategory.RootID 
""")

print "compiling data..."

def CreateThemeUrl(theme):
    theme = theme.lstrip()
    theme_url = 'http://rynok.yottos.com/%s' % theme.replace(' ', '_')
    return '<a href="%s">%s</a>' % (theme_url, theme)

proc = Popen([COMPILER, argv[1]], stdin=PIPE)
for row in c:
    theme_url = CreateThemeUrl(row[3])
    line = '%s\t%s\n' % (row[0], theme_url)
    proc.stdin.write(line.encode('utf-8'))
proc.stdin.close()
proc.wait()
