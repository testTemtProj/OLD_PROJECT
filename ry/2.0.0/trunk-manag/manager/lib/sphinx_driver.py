#coding: utf-8
import pymongo
if __name__ == '__main__':
    db = pymongo.Connection("213.186.119.121:27017, 213.186.119.121:27018, 213.186.119.121:27019").rynok
    vendors = {}
    categorie = {}
    for cat in db.Category.find({'isLeaf':True}):
        categorie[cat['ID']] = cat['Name'].encode("utf-8")
    for vendor in db.Vendors.find():
        if vendor.has_key("id"):
            vendors[vendor['id']] = vendor['name']    
    lots = db.Products
    id = 0
    print """<?xml version="1.0" encoding="utf-8"?><sphinx:docset>
<sphinx:schema>
<sphinx:field name="title"/>
<sphinx:field name="description"/>
<sphinx:field name="vendor"/>
<sphinx:field name="category"/>
<sphinx:attr name="price" type="int"/>
<sphinx:attr name="vendor_attr" type="string"/>
<sphinx:attr name="shopId" type="int"/>
<sphinx:attr name="categoryId" type="int"/>
<sphinx:attr name="geolist" type="multi"/>
<sphinx:attr name="paramslist" type="multi"/>
</sphinx:schema>"""
    for p in lots.find():
        id += 1
        p["id_int"] = id        
        lots.save(p)
        if categorie.has_key(p['categoryId']):
            categor = categorie[p['categoryId']]
        else:
            categor = "None"
        if vendors.has_key(p['vendor']):
            vendor = vendors[p['vendor']]
        else:
            vendor = -1
        print """<sphinx:document id="%s">
<title><![CDATA[%s]]></title>
<description><![CDATA[%s]]></description>
<vendor><![CDATA[%s]]></vendor>
<category><![CDATA[%s]]></category>
<price><![CDATA[%s]]></price>
<vendor_attr><![CDATA[%s]]></vendor_attr>
<shopId><![CDATA[%s]]></shopId>
<categoryId><![CDATA[%s]]></categoryId>
<geolist></geolist>
<paramslist></paramslist>
</sphinx:document>"""%(p["id_int"], p["title"].encode("utf-8"), p.get("description", "").encode("utf-8"), vendor.encode("utf-8"), categor ,p["price"], p["vendor"], p["shopId"], p["categoryId"])
    print "</sphinx:docset>" 
