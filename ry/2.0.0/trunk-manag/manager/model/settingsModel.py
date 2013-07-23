# coding: utf-8
from manager.model.baseModel import Base

class SettingsModel():

    setting_collection = Base.settings_collection

        
    @staticmethod
    def save_common_settings(data):
        
        """
            Функция для сохранения основных настроек
            
            Передаеться:
                data - массив основных настроек
        """
        
        SettingsModel.setting_collection.update({'name': data['name']},{'$set': data }, upsert = True)

    
    @staticmethod
    def get_all():
        
        """
            Функция для получения всех настроек
            
            Возвращает:
                settings - массив всех настроек
        """
        
        settings = []
        for x in SettingsModel.setting_collection.find():
            settings.append(x)
        return settings
