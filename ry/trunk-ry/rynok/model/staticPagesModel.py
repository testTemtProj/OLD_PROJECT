# coding: utf-8
from rynok.model.baseModel import Base
from rynok.model.navigation import NavigationAbstract

class StaticPagesModel(NavigationAbstract):
    static_pages_collection = Base.static_pages_collection

    @staticmethod
    def get_by_id(page_id, with_content=False):
        return StaticPagesModel.static_pages_collection.find_one({'id': int(page_id)}, {'content' : with_content}, slave_okay=True)
    

    @staticmethod
    def get_by_slug(slug):
        return StaticPagesModel.static_pages_collection.find_one({'slug': unicode(slug)}, slave_okay=True)

    
    @staticmethod
    def get_by_parent_id(parent_id):
        return StaticPagesModel.static_pages_collection.find({'parent_id': int(parent_id)}, slave_okay=True)
