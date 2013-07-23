import pymongo
import time
from datetime import datetime as dt

obgectsForAdd = []

def getDataForPresentation(db, id):
    for category in db.Category.find({'ParentID':id}):
        for product in db.Products.find({'CategorID':category['ID']}).sort('Weight',-1).limit(9):
            if len(obgectsForAdd) < 9:
                obgectsForAdd.append(product)
            else:
                i = 0
                for x in obgectsForAdd:
                    if x['Weight'] < product['Weight']:
                       obgectsForAdd[i] = product
                    i += 1
        if category['ID'] != category['ParentID']:
            getDataForPresentation(db, category['ID'])
        
    return obgectsForAdd

if __name__ == '__main__':
    count = 0
    db = pymongo.Connection(['10.0.0.8:27018, 10.0.0.8:27017, 10.0.0.8:27019']).rynok
    t1 = time.time()
    print "Start Parsing..."
    db.Presentation.remove({'IsStatic':0})
    print "Data Base has wiped..."
    statucCount = db.Presentation.find().count()
    print "Static filds left - " + str(statucCount)
    if statucCount == 0:
        wtf = getDataForPresentation(db,0)
        i = 0
        for x in wtf:
            db.Presentation.insert({'LotID':x['LotID'], 'Price': x['Price'], 'CategorID':0, 'Title':x['Title'], 'ImageURL': x['ImageURL'], 'URLconf':x['URLconf'], 'IsStatic': 0, 'Position': i, 'Type': 'Lot'})
            count+=1
            i += 1
        obgectsForAdd = []
        for category in db.Category.find():
            i = 0
            ID = category['ID']
            wtf = getDataForPresentation(db,ID)
            for x in wtf:
                db.Presentation.insert({'LotID':x['LotID'], 'Price': x['Price'], 'CategorID':ID, 'Title':x['Title'], 'ImageURL': x['ImageURL'], 'URLconf':x['URLconf'], 'IsStatic': 0, 'Position': i, 'Type': 'Lot'})
                count+=1
                i += 1
            obgectsForAdd = []
    else:
        wtf = getDataForPresentation(db,0)
        i = 0
        for x in wtf:
            if i < 9:
                if db.Presentation.find_one({'CategorID': 0, 'Position': i}):
                    if db.Presentation.find_one({'CategorID': 0, 'Position': i})['LotID'] != x['LotID']:
                        db.Presentation.insert({'LotID':x['LotID'], 'Price': x['Price'], 'CategorID':0, 'Title':x['Title'], 'ImageURL': x['ImageURL'], 'URLconf':x['URLconf'], 'IsStatic': 0, 'Position': i, 'Type': 'Lot'})
                        count+=1
            i += 1
        obgectsForAdd = []
        for category in db.Category.find():
            if category['CountLot'] == 0:
                i = 0
                ID = category['ID']
                wtf = getDataForPresentation(db,ID)
                for x in wtf:
                    if i < 9:
                        if db.Presentation.find_one({'CategorID': ID, 'Position': i}):
                            if db.Presentation.find_one({'CategorID': ID, 'Position': i})['LotID'] != x['LotID']:
                                db.Presentation.insert({'LotID':x['LotID'], 'Price': x['Price'], 'CategorID':ID, 'Title':x['Title'], 'ImageURL': x['ImageURL'], 'URLconf':x['URLconf'], 'IsStatic': 0, 'Position': i, 'Type': 'Lot'})
                                count+=1
                    i += 1
                obgectsForAdd = []
    t2 = time.time()
    print 'Lots added ' + str(count)
    print "Done in time: " + str(t2-t1) + " sec"
        
