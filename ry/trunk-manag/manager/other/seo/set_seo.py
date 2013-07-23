# coding: utf-8

"""
	Скрипт необходимый для создания seo для категорий рекурсивно обходит категории
	и у каждой дочерней категории meta теги являються названиями 
	родительских категорий
"""

import pymongo as p
from pylons import config

db_str = config.get('mongo_database', 'rynok')
connection_str = [config.get('mongo_host', '10.0.0.8:27018, 10.0.0.8:27017, 10.0.0.8:27019')]

print db_str

DB = p.Connection(connection_str)[db_str]

keywords = u''

def get_seo_kaywords(id, parent_id, is_first = True):
	global keywords
	if is_first:
		keywords = u''
		keywords += DB.Category.find_one({'ID': id})['Name']
	
	if int(parent_id) != 0:
		category = DB.Category.find_one({'ID': parent_id})
		keywords += ", " + category['Name']
		get_seo_kaywords(category['ID'], category['ParentID'], False)
	
	return keywords

def set_seo(id = 0):
	p_cat = DB.Category.find({'ParentID':id})
	for x in p_cat:
		seo_str = get_seo_kaywords(x['ID'], x['ParentID'])
		print seo_str
		DB.Category.update({'ID':x['ID']}, {"$set":{'Title': u'Yottos Рынок | '+x['Name'],'MetaKey':seo_str, 'Description': u'Рынок Yottos объединяет все интернет-магазины в одном месте, помогает покупателям найти самое выгодное предложение, а продавцам — заинтересованных клиентов.'}})
		set_seo(x['ID'])
	return

if __name__ == '__main__':
    set_seo()
