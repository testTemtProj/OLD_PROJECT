# coding: utf-8
import pymongo
import time
import pyodbc
import random
from trans import trans
from datetime import datetime as dt
if __name__ == '__main__':
    db = pymongo.Connection(['10.0.0.8:27018, 10.0.0.8:27017, 10.0.0.8:27019']).rynok
#    db = pymongo.Connection().test
    category = {}
    cnxn = pyodbc.connect('DRIVER={SQL Server};SERVER=213.186.119.106;DATABASE=1gb_YottosRynok;UID=web;PWD=odif8duuisdofj')
    cursor = cnxn.cursor()
    data = cursor.execute("select * from Category")
    """
    /****** Сценарий для команды SelectTopNRows среды SSMS  ******/
SELECT TOP 1000 [Title]
      ,[CategoryID]
      ,[Descript]
      ,[ParentID]
      ,[isLeaf]
      ,[icoURL]
      ,[RootID]
      ,[ReferencesStrings]
      ,[Keywords]
      ,[MetaDescription]
      ,[CategoryID_int]
  FROM [1gb_YottosRynok].[dbo].[Category]
    """
    for c in data:
        category[c.CategoryID] = c.CategoryID_int
#    print category
#    exit(1)
    cnxn = pyodbc.connect('DRIVER={SQL Server};SERVER=213.186.119.106;DATABASE=1gb_YottosRynok;UID=web;PWD=odif8duuisdofj')
    cursor = cnxn.cursor()
    data = cursor.execute("select * from Category")
    t1 = time.time()
    print "Start import categories.."
    count = 0
    db.Category.ensure_index("ID")
    db.Category.ensure_index("ParentID")
    for x in data:
        try:
#            if count>10000:
#                break;
            item = {}
            item['CountLot'] = 0
            item['ID'] = x.CategoryID_int
            if category.has_key(x.ParentID):
                item['ParentID'] = category[x.ParentID]
            else:
                item['ParentID'] = 0
#                continue
            item['Name'] = x.Title.decode('cp1251')
            item['Translited'] = trans(item['Name'])[0].strip().replace("(", " ").replace(")", " ").replace(" ", "_").replace("-", "_").replace(",", "").replace(".", "")
#            try:
#                item['Title'] = x.Descript.decode('cp1251')
#            except:
#                pass
            if item['ID']==item['ParentID']:
                continue
            print "Count: %s" %count
            #db.Category.insert(item)
            db.Category.update({"ID":item['ID']}, {"$set":item}, upsert=True)
            count +=1
        except Exception, ex:
            print "Error on %s" %ex
    print "End import"
    t2 = time.time()
    print "Time: %s\nCount: %s\nCount per time: %s"%(t2-t1, count, (t2-t1)/count)
    execfile("counting_lot.py")

