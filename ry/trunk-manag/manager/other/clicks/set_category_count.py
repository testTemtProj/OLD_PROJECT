# coding: utf-8

from pymongo import  Connection 
cats = Connection('10.0.0.8:27017').rynok.Category
products = Connection('10.0.0.8:27017').rynok.Products
new_products = Connection('10.0.0.8:27017').rynok.NewProducts
popular_products = Connection('10.0.0.8:27017').rynok.PopularProducts


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

def set_last_products():
    # лимит надо доставать из базы настроек
    limit = 50
    result = []

    pr = products.find().sort('$natural', -1)

    if pr.count():
        last_cat_id = products[0]['categoryId']
        new_products.remove()
    else:
        return 

    for product in pr:
        if len(result) >= limit:
            break

        if product['categoryId'] == last_cat_id:
            continue

        result.append(product)

        last_cat_id = product['categoryId']
    
    new_products.insert(result)
    return 

def set_popular_products():
    # количество категория и количество товаров на категорию доставать из базы настроек
    count_cats = 5
    count_per_cat = 7
    result = []

    x = 1 
    for cat in cats.find({'isLeaf': True, 'count':{'$gt': count_per_cat}}).sort('popularity', -1).limit(count_cats):
        tempo = products.find(fields=['title', 'id', 'picture', 'price', 'advert_id', 'vendor', 'categoryId', 'shopId', 'url'], spec={'categoryId': cat['ID']}).sort('popularity', -1).limit(count_per_cat)
        for item in tempo:
            item['counter'] = x
            item['category'] = cat['Name']
            result.append(item)
        x += 1
    popular_products.remove()
    popular_products.insert(result)
        
    return 

