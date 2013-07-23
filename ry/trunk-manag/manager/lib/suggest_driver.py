#coding: utf-8
#CSV-PIPE драйвер для связи MongoDB с Suggest Compiller Dict
import pymongo
import itertools
from sys import getsizeof
if __name__ == '__main__':
    db = pymongo.Connection('10.0.0.8:27017').rynok
    category = {}    
    count = 0
    total = float(db.Products.find().count())
    print "Total products: %s"%total
    for cat in db.Category.find({'isLeaf':True}):
        category[cat['ID']] = {'name' : cat['Name'].encode("utf-8"), 'url':cat['URL'].encode("utf-8")}     
    try:            
        f = file("dict.txt", "w+")
        for p in db.Products.find():
            if count%10==0:
                print "Progress: %s %%, count: %s" %((count/total)*100, count)            
            count += 1  
            #continue  
            try:    
                if category.has_key(p['categoryId']):
                    categor = category[p['categoryId']]
                else:
                    categor = {name:"None", url:'/'}
            except:
                continue
            li = []
            for element in p["title"].encode("utf-8").strip().split():
                    if len(element) > 3:
                            li.append(element)
            i = 1
            c = len(li)   
            if c>3:
                continue     
            m = []
            while i <= c:
                    m = m + list(itertools.permutations(li, i))
                    i = i + 1
            for element in m:                
                    f.write("%s\t<a href='%s/'>%s</a>\n"%(' '.join(element), categor['url'], categor['name']))
                    f.flush()
    except Exception, ex:
        print ex
    finally:            
        f.close()
        print "End"