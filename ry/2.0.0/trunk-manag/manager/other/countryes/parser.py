# coding: utf-8
import pymongo
from BeautifulSoup import BeautifulSoup
import re

escape = [u'Пользовательское соглашение',u'Мобильная версия',u'Статистика',u'Обратная&nbsp;связь',u'Реклама',u'Для магазинов',u'Яндекс',u'0 - 9',u'None',u'маркет',u'Поиск',u'Почта',u'Карты',u'Маркет',u'Новости',u'Словари',u'Блоги',u'Видео',u'Картинки',u'Авто',u'Афиша',u'Деньги',u'Каталог',u'Мой&nbsp;Круг',u'Музыка',u'Народ',u'Недвижимость',u'Открытки',u'Погода',u'Пробки',u'Работа',u'Расписания',u'Телепрограмма',u'Услуги',u'Фотки',u'Я.ру',u'Программы',u'Все&nbsp;сервисы',u'мои запросы',u'Почта',u'РСЯ',u'Паспорт',u'Сменить пароль',u'Выход',u'Настройка',u'Помощь',u'Список покупок',u'Мои оценки и&nbsp;отзывы',u'Посещённые магазины',u'Регион',u'Каталог производителей']
PATH = 'html/'
MONGO_CONNECT = ['10.0.0.8:27018', '10.0.0.8:27017', '10.0.0.8:27019']

if __name__ == '__main__':
	db = pymongo.Connection(MONGO_CONNECT).rynok
	id = 0
	doc = open(PATH+'2.html','r')
	soup = BeautifulSoup(''.join(doc))
	id = db.Venders.find().sort('id',-1).next()['id']+1
	for x in soup.findAll('a'):
		try:
			if x.string not in escape and len(x.string) > 1:
				db.Venders.insert({'id':id, 'name': x.string})
				id += 1
		except Exception, ex:
			pass
			
