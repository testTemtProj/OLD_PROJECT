# coding: utf-8

"""
	Скрипт нужен для создания дампа памяти(в файл) со списком категорий
	Распарсивает сохраненный файлик с Wikipedia
"""

from BeautifulSoup import BeautifulSoup
import re
import pickle

PATH = 'html/'

def saveData(data, filename):
    file = open(filename, 'w')
    pickle.dump(data, file)
    file.close()
    
def restoreData(filename):
    file = open(filename, 'r')
    data = pickle.load(file)
    file.close()
    return data

if __name__ == '__main__':
    
    escape = [u'↑',u'Regions and territories: Abkhazia',u'Regions and territories: Kosovo',u'Regions and territories: Western Sahara',u'Regions and territories: South Ossetia',
              u'Cyprus',u'Regions and territories: Nagorno-Karabakh',u'Regions and territories: Trans-Dniester',u'Regions and territories: Somaliland',u'Малави перестала признавать суверенитет Тайваня',
              u'Сам себе король, сам себе страна',u'Непризнанные государства европейской периферии и пограничья',u'По соседству с Англией продается государство',u'Сколько стран в Европе?',
              u'Морская земля',u'непризнанным государством',u'[10]',u'[11]',u'[12]',u'[13]',u'[14]', u'заморская территория', u'непризнанной',u'частично признанными',
              u'заморская территория Великобритании', u'коронная земля', u'заморский регион Франции',u'Французские Южные и Антарктические Территории',u'непризнанное государство',
              u'частично признанное государство',u'протекторатом', u'[9]',u'штат',u'Британская территория в Индийском океане']
    doc = open(PATH+'2.html','r')
    soup = BeautifulSoup(''.join(doc))
    countries = []
    for x in soup.findAll(True):
        if x.name == 'ol':
            for y in x.findAll('a'):
                if y.string not in escape and y.string != None:
                    countries.append(str(y.string).decode('utf-8'))
    
    saveData(countries,'countries')
