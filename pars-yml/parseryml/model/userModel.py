# coding: utf-8
from parseryml.model.baseModel import Base

class UserModel():
    
    def __init__(self):
        
        """
            Конструктор модели  
            
            Инициализирует переменные:
                db - объект главной модели
                users_collection - объект колекции пользователя
        """
        
        base_model = Base()
        self.users_collection = base_model.get_users_collection()
        
    def check_user_pwd(self,login,pwd):
        
        """
            Функция для проверки логина и пароля пользователя
            
            Получает:
                login - логин пользователя
                pwd - пароль пользователя
        """
        
        user = self.users_collection.find_one({'login':login, 'password':pwd})
        print self.users_collection
        try:
            user['login']
            return True
        except:
            return False
