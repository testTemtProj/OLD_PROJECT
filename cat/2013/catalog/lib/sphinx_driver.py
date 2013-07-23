#coding: utf-8
#-*- coding=utf-8 -*-

import pymongo

if __name__ == '__main__':
    #db = pymongo.Connection().catalog
    db = pymongo.Connection(['10.0.0.8:27017','10.0.0.8:27018','10.0.0.8:27019']).catalog
    categorie = {}
    for cat in db.category.find({'is_leaf':True}):
        categorie[cat['id']] = cat['title'].encode("utf-8")
    links = db.site
    id = 0
    print """<?xml version="1.0" encoding="utf-8"?><sphinx:docset>
<sphinx:schema>
<sphinx:field name="title_ru"/>
<sphinx:field name="title_en"/>
<sphinx:field name="title_uk"/>
<sphinx:field name="description"/>
<sphinx:field name="description_ru"/>
<sphinx:field name="description_en"/>
<sphinx:field name="description_uk"/>
<sphinx:field name="category"/>
<sphinx:attr name="category_id" type="int"/>
</sphinx:schema>"""
    for p in links.find({'$and':[{'checked':True},{'avaible':True}]}):
        id += 1
        p["id"] = id        
        links.save(p)
        if categorie.has_key(p['category_id']):
            categor = categorie[p['category_id']]
        else:
            categor = "None"
        print """<sphinx:document id="%s">
<title_ru><![CDATA[%s]]></title_ru>
<title_en><![CDATA[%s]]></title_en>
<title_uk><![CDATA[%s]]></title_uk>
<description_ru><![CDATA[%s]]></description_ru>
<description_en><![CDATA[%s]]></description_en>
<description_uk><![CDATA[%s]]></description_uk>
<category><![CDATA[%s]]></category>
<category_id><![CDATA[%s]]></category_id>
</sphinx:document>"""%(p.get("id"), p.get("name_ru").encode("utf-8"), p.get("name_en").encode("utf-8"), p.get("name_uk").encode("utf-8"), p.get("description_ru", "").encode("utf-8"),p.get("description_en", "").encode("utf-8"),p.get("description_uk", "").encode("utf-8"), categor, p.get("category_id"))
    print "</sphinx:docset>" 
