#!/usr/bin/python
from pymongo import Connection

cats = Connection('10.0.0.8:27017').rynok.Category

def update(root_id=0, url=''):

    for cat in cats.find({"ParentID": root_id}):
        cat["URL"] = url + '/' + cat["Translited"].replace(",", "").replace("/", "")
        cats.save(cat) 
        update(cat["ID"], cat["URL"])

    return

update()
