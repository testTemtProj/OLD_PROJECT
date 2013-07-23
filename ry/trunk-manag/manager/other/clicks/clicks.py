# coding: utf-8
import pymongo as p

#TODO: Вынести таском в celery

class Clicks():
    def __init__(self):
        
        """
            Конструктор класа
            
            Инициализирует переменные:
                db - объект базы данных
        """

        self.db = p.Connection(['10.0.0.8:27018', '10.0.0.8:27017', '10.0.0.8:27019']).rynok
    
    def start(self):
        
        """
            Функция для подсчета популярности товара, категории,
            производитеоя, магазина.
        """
        
        result = False
        for counter in [0,1,2]:
            if counter == 0:
                collection = self.db.clicks
            elif counter == 1:
                collection = self.db.clicks.error
            elif counter == 2:
                collection = self.db.clicks.rejected

            for click in collection.find({'ch': {'$exists': False}}):
                result = True
                click['ch'] = True
                collection.save(click)
                if 'offer' in click:
                    try:
                        self.db.Products.update({'id': click['offer']},{ '$inc' : { 'popularity' : 1 } })
                    except:
                        self.db.Products.update({'id': click['offer']},{'$set':{'popularity': 1}})

                if 'vendor' in click:
                    try:
                        self.db.Vendors.update({'id': click['vendor']},{ '$inc' : { 'popularity' : 1 } })
                    except:
                        self.db.Vendors.update({'id': click['vendor']},{'$set': {'popularity': 1}})

                if 'categoryId' in click:
                    try:
                        self.db.Category.update({'ID': click['categoryId']},{ '$inc' : { 'popularity' : 1 } })
                    except:
                        self.db.Category.update({'ID': click['categoryId']},{'$set': {'popularity': 1}})
                        
                if 'shopId' in click:
                    try:
                        self.db.Market.update({'id': click['shopId']}, { '$inc' : { 'popularity' : 1 } })
                    except:
                        self.db.Market.update({'id': click['shopId']}, {'$set': {'popularity': 1}})
        return result
    
    def clear(self):
        
        """
            Функция для очистки популярности категоирй, производителей, 
            товаров, магазинов(используеться при отладке)
        """
        
        for x in self.db.clicks.find():
            try:
                del x['ch']
                self.db.clicks.save(x)
            except:
                pass
            self.db.Products.update({'id': x['offer']},{'$set':{'popularity': 0}})
            self.db.Market.update({'id': x['shopId']},{'$set':{'popularity': 0}})
            self.db.Vendors.update({'id': x['categoryId']},{'$set':{'popularity': 0}})
            self.db.Category.update({'id': x['vendor']},{'$set':{'popularity': 0}})

if __name__ == '__main__':
    
    """
        Старт обработки кликов и установки популярности товара
    """
    
    Clicks().start()