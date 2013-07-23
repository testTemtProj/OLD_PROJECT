# This Python file uses the following encoding: utf-8
from pylons import app_globals

class StatisticReport():
    
    def __init__(self):
        self.db = app_globals.db
    
    def allAdvertiseScriptsSummary(self, user_login, dateStart = None, dateEnd = None):
        """Возвращает суммарную статистику по всем площадкам пользователя user_id"""
        reduce = '''function(o,p) {
                p.advTitle = (o.domain || " ") + (o.title || " ");
                if (o.isOnClick){
                p.clicks += o.clicks || 0;
                p.unique += o.clicksUnique || 0
                p.tiaser_totalCost += o.teaser_totalCost || 0;
                p.impressions += o.impressions_block || 0;
                p.banner_impressions += o.banner_impressions || 0;
                p.banner_totalCost += o.banner_totalCost || 0;
                p.banner_unique += o.banner_clicksUnique || 0;
                }
                else{
                p.imp_banner_totalCost += o.banner_totalCost || o.totalCost || 0;
                p.imp_banner_impressions += o.banner_impressions || 0;
                }
                p.totalCost += o.totalCost || 0;
            }'''
        condition = {'user': user_login}
        dateCondition = {}
        if dateStart <> None: dateCondition['$gte'] = dateStart
        if dateEnd <> None:   dateCondition['$lte'] = dateEnd
        if len(dateCondition) > 0:
            condition['date'] = dateCondition
        
        res = self.db.stats_daily_adv.group(['adv'],
                                       condition,
                                       {'advTitle': '',
                                        'clicks':0,
                                        'unique':0,
                                        'banner_impressions':0,
                                        'banner_totalCost':0,
                                        'banner_unique':0,
                                        'impressions':0,
                                        'tiaser_totalCost':0,
                                        'imp_banner_impressions':0,
                                        'imp_banner_totalCost':0,
                                        'totalCost':0},
                                       reduce)
        return res

    def statUserGroupedByDate(self, user, dateStart = None, dateEnd = None):
        """ Возвращает список {дата,уникальных,кликов,показов,сумма} 
            для пользователя или списка пользователей.
            
            Формат одной структуры в списке:
            
                {'date': datetime.datetime,
                 'unique': int,
                 'clicks': int,
                 'impressions': int,
                 'summ': float}
        
        """
         
        reduce = '''function(o,p) {
                p.domain = o.domain || " ";
                p.title = o.title || " ";
                if (o.isOnClick){
                p.clicks += o.clicks || 0;
                p.unique += o.clicksUnique || 0
                p.tiaser_totalCost += o.teaser_totalCost || 0;
                p.impressions += o.impressions_block || 0;
                p.banner_impressions += o.banner_impressions || 0;
                p.banner_totalCost += o.banner_totalCost || 0;
                p.banner_unique += o.banner_clicksUnique || 0;
                }
                else{
                p.imp_banner_totalCost += o.banner_totalCost || o.totalCost || 0;
                p.imp_banner_impressions += o.banner_impressions || 0;
                }
                p.summ += o.totalCost || 0;
            }'''
        
        condition = {'user': {'$in': user if isinstance(user, list) else [user]}}
        dateCondition = {}
        if dateStart <> None: dateCondition['$gte'] = dateStart
        if dateEnd <> None:   dateCondition['$lte'] = dateEnd
        if len(dateCondition) > 0:
            condition['date'] = dateCondition
        return [{'date': x['date'],
                 'unique': x['unique'],
                 'banner_unique': x['banner_unique'],
                 'clicks': x['clicks'],
                 'impressions': x['impressions']-x['banner_impressions'],
                 'imp_banner_impressions': x['imp_banner_impressions'],
                 'tiaser_totalCost': x['tiaser_totalCost'],
                 'imp_banner_totalCost': x['imp_banner_totalCost'],
                 'banner_totalCost':x['banner_totalCost'],
                 'summ': x['summ']}
                 for x in self.db.stats_daily_adv.group(['date'],
                                                   condition,
                                                   {'clicks':0,
                                                    'banner_unique':0,
                                                    'unique':0,
                                                    'impressions':0,
                                                    'imp_banner_impressions':0,
                                                    'banner_impressions':0,
                                                    'tiaser_totalCost':0,
                                                    'imp_banner_totalCost':0,
                                                    'banner_totalCost':0,
                                                    'summ':0},
                                                   reduce)]
    

    def statAdvGroupedByDate(self, adv_guid, dateStart = None, dateEnd = None):
        """ Возвращает список {дата,уникальных,кликов,показов,сумма} 
            для одного РБ.
            
            Формат одной структуры в списке:
            
                {'date': datetime.datetime,
                 'unique': int,
                 'clicks': int,
                 'impressions': int,
                 'summ': float}
        
            Параметр adv_guid -- коды одного РБ,
            по которым будет считаться статистика.
        """
         
        reduce = '''function(o,p) {
                p.domain = o.domain || " ";
                p.title = o.title || " ";
                if (o.isOnClick){
                p.clicks += o.clicks || 0;
                p.unique += o.clicksUnique || 0
                p.tiaser_totalCost += o.teaser_totalCost || 0;
                p.impressions += o.impressions_block || 0;
                p.banner_impressions += o.banner_impressions || 0;
                p.banner_totalCost += o.banner_totalCost || 0;
                p.banner_unique += o.banner_clicksUnique || 0;
                }
                else{
                p.imp_banner_totalCost += o.banner_totalCost || o.totalCost || 0;
                p.imp_banner_impressions += o.banner_impressions || 0;
                }
                p.summ += o.totalCost || 0;
            }'''
        

        condition = {'adv': adv_guid }
        dateCondition = {}
        if dateStart <> None: dateCondition['$gte'] = dateStart
        if dateEnd <> None:   dateCondition['$lte'] = dateEnd
        if len(dateCondition) > 0:
            condition['date'] = dateCondition
    
        return [{'date': x['date'],
                 'unique': x['unique'],
                 'banner_unique': x['banner_unique'],
                 'clicks': x['clicks'],
                 'impressions': x['impressions']-x['banner_impressions'],
                 'imp_banner_impressions': x['imp_banner_impressions'],
                 'tiaser_totalCost': x['tiaser_totalCost'],
                 'imp_banner_totalCost': x['imp_banner_totalCost'],
                 'banner_totalCost':x['banner_totalCost'],
                 'summ': x['summ']}
                 for x in self.db.stats_daily_adv.group(['date'],
                                                   condition,
                                                   {'clicks':0,
                                                    'banner_unique':0,
                                                    'unique':0,
                                                    'impressions':0,
                                                    'imp_banner_impressions':0,
                                                    'banner_impressions':0,
                                                    'tiaser_totalCost':0,
                                                    'imp_banner_totalCost':0,
                                                    'banner_totalCost':0,
                                                    'summ':0},
                                                   reduce)]

    def statAdvByDate(self, user, dateStart = None, dateEnd = None):
        """ Возвращает список {дата,уникальных,кликов,показов,сумма} 
            для пользователя.
            
            Формат одной структуры в списке:
            
                {'date': datetime.datetime,
                 'unique': int,
                 'clicks': int,
                 'impressions': int,
                 'summ': float}
        
            Параметр adv_guid -- нескольких РБ,
            по которым будет считаться статистика.
        """
         
        reduce = '''function(o,p) {
                p.clicks += o.clicks || 0;
                p.domain = o.domain || " ";
                p.title = o.title || " ";
                p.data.push([ (o.date) ,(o.totalCost || 0)]);
            }''' 
        

        condition = {'user': user}
        dateCondition = {}
        if dateStart <> None: dateCondition['$gte'] = dateStart
        if dateEnd <> None:   dateCondition['$lte'] = dateEnd
        if len(dateCondition) > 0:
            condition['date'] = dateCondition
    
        return [{'guid': x['adv'],
                 'domain': x['domain'],
                 'title': x['title'],
                 'data': x['data']}
                 for x in self.db.stats_daily_adv.group(['adv'],
                                                   condition,
                                                   {'title': '', 'domain': '', 'data': []},
                                                   reduce)]
