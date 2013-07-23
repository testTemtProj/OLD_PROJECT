# This Python file uses the following encoding: utf-8
from pylons import app_globals

class StatisticReport():
    
    def __init__(self):
        self.db = app_globals.db
    
    def statGroupedByDate(self, adv_guid, dateStart = None, dateEnd = None):
        """ Возвращает список {дата,уникальных,кликов,показов,сумма} 
            для одной или нескольких выгрузок.
            
            Формат одной структуры в списке:
            
                {'date': datetime.datetime,
                 'unique': int,
                 'clicks': int,
                 'impressions': int,
                 'summ': float}
        
            Параметр adv_guid -- коды одного или нескольких информеров,
            по которым будет считаться статистика. Может быть строкой 
            или списком строк
        """
         
        reduce = 'function(o,p) {' \
            '    p.clicks += o.clicks || 0;' \
            '    p.unique += o.clicksUnique || 0;' \
            '    p.impressions += o.impressions || 0;' \
            '    p.summ += o.totalCost || 0;' \
            '}' 
        
        condition = {'adv': {'$in': adv_guid if isinstance(adv_guid, list) else [adv_guid]}}
        dateCondition = {}
        if dateStart <> None: dateCondition['$gte'] = dateStart
        if dateEnd <> None:   dateCondition['$lte'] = dateEnd
        if len(dateCondition) > 0:
            condition['date'] = dateCondition
    
        return [{'date': x['date'],
                 'unique': x['unique'],
                 'clicks': x['clicks'],
                 'impressions': x['impressions'],
                 'summ': x['summ']}
                 for x in self.db.stats_daily_adv.group(['date'],
                                                   condition,
                                                   {'clicks':0, 'unique':0, 'impressions':0, 'summ':0},
                                                   reduce)]
