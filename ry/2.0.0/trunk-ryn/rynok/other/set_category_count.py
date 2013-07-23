#!/usr/bin/python
# coding: utf-8

from pymongo import  Connection

cats = Connection('10.0.0.8:27017').rynok.Category
products = Connection('10.0.0.8:27017').rynok.Products

def count_categories():
    categories = cats.find({'isLeaf': True})
    for cat in categories:
        count = products.find({'categoryId': cat['ID']}).count()
        cat['count'] = count
        cats.save(cat)

def count_products(root):

    root_cat = cats.find_one({'ID': root})

    if root_cat['isLeaf']:
		try:
			return root_cat['count']
		except:
			return 0

    childrens = cats.find({'ParentID': root})

    count = 0

    for children in childrens:
        count += count_products(children['ID'])

    root_cat['count'] = count
    cats.save(root_cat)
    
    return count

def set_popular(root):

    root_cat = cats.find_one({'ID': root})

    if root_cat['isLeaf']:
        if root_cat.has_key('popularity'):
            return root_cat['popularity']
        else:
			return 0

    childrens = cats.find({'ParentID': root})

    count = 0

    for children in childrens:
        count += set_popular(children['ID'])

    root_cat['popularity'] = count
    cats.save(root_cat)
    
    return count

def set_isLeaf(root):

    root_cat = cats.find_one({'ID': root})
    
    childrens = cats.find({'ParentID': root})

    if childrens.count():
        root_cat['isLeaf'] = False
    else:
        root_cat['isLeaf'] = True 

    cats.save(root_cat)

    for ch in childrens:
        set_isLeaf(ch['ID'])

set_isLeaf(0)
count_categories()
count_products(0)
