# coding: utf-8
from rynok.model.baseModel import Base
from rynok.model.categoriesModel import CategoriesModel

class SettingsModel():
    settings_collection = Base.settings_collection


    @staticmethod
    def get_main_page_settings():
        return SettingsModel.settings_collection.find_one({'name': 'mainPage'})

    
    @staticmethod
    def get_common_settings():
        return SettingsModel.settings_collection.find_one({'name': 'common'})
    

    @staticmethod
    def get_search_page_settings():
        return SettingsModel.settings_collection.find_one({'name': 'searchPage'})


    @staticmethod
    def get_footer_settings():
        common_settings = SettingsModel.get_common_settings()
        footer_settings = []
        for item in common_settings['fields']:
            footer_settings.append(item)

        return footer_settings


    @staticmethod
    def wishlist_enabled():
        common_settings = SettingsModel .get_common_settings()
        if 'vishlist' in common_settings:
            return common_settings['vishlist']

        return False


    @staticmethod
    def get_popular_block_settings():
        main_page_settings = SettingsModel.get_main_page_settings()
        return {'categories': main_page_settings['colCatsPopGoods'], 'per_category' : main_page_settings['colPopGoods']}


    @staticmethod
    def get_new_block_settings():
        main_page_settings = SettingsModel.get_main_page_settings()
        return {'products' : main_page_settings['colsNewGoods']}


    @staticmethod
    def get_main_page_categories():
        categories_collection = CategoriesModel.CategoriesCollection
        main_page_settings = SettingsModel.get_main_page_settings()
        category_names = main_page_settings['fields']
        categories_size = main_page_settings['type']
        count_categories = 6 if categories_size == '3x2' else 9
        categories = []
        for category_name in category_names:
            category = categories_collection.find_one({'Name':category_name, 'ParentID': 0, 'count': {'$gt': 0}})
            if category:
                categories.append(category)

        if len(categories) < count_categories:
            count_of_missing_categories = count_categories - len(categories)
            missing_categories = categories_collection.find({'Name': {'$nin':category_names}, 'ParentID':0, 'count':{'$gt': 0}}).limit(count_of_missing_categories)
            for category in missing_categories:
                categories.append(category)

        return categories


    @staticmethod
    def get_main_page_banner():
        main_page_settings = SettingsModel.get_main_page_settings()
        return main_page_settings['baner']


    @staticmethod
    def get_search_page_banner():
        search_page_settings = SettingsModel.get_search_page_settings()
        return search_page_settings['baner']
