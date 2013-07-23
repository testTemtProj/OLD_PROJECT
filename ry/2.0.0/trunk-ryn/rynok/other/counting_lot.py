# coding: utf-8
import pymongo
import time
if __name__ == '__main__':
    db = pymongo.Connection(['10.0.0.8:27018, 10.0.0.8:27017, 10.0.0.8:27019']).rynok
    cats = db.Category
    lots = db.Products
    t1 = time.time()   
    id = 0
#    lots.ensure_index("id_int", 1)
    print "Start update lot_id lots"
    for p in lots.find():
#        if "id_int" in p.keys():
#            id = p["id_int"]
        id += 1
        p["id_int"] = id
        lots.save(p)
        print id
#    for cat in cats.find():
#        id = cat['ID']
#        count = lots.find({"CategorID":id}).count()
#        cat['CountLot'] = count
#        t += count
#        print "by %s count%s" %(id, count)
#        cats.save(cat)
    print "End import"
    t2 = time.time()
    print "Time: %s\nCount: %s\nCount per time: %s"%(t2-t1, id, (t2-t1)/id)
