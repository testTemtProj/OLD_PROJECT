# This Python file uses the following encoding: utf-8
import pymongo
from pylons import app_globals, config

class Campaign(object):
    "Класс описывает рекламную кампанию, запущенную в GetMyAd"
    
    class NotFoundError(Exception):
        'Кампания не найдена'
        def __init__(self, id):
            self.id = id
        
    
    def __init__(self, id):
        #: ID кампании
        self.id = id.lower()
        #: Заголовок рекламной кампании
        self.title = ''
        #: Является ли кампания социальной рекламой
        self.social = False
        #: Является ли кампания социальной рекламой
        self.project = ''
        #: Добавлять ли к ссылкам предложений маркер yottos_partner=...
        self.yottos_partner_marker = True
        #: Добавлять ли к ссылкам предложений маркер для Attractor...
        self.yottos_attractor_marker = True
        #: Время последнего обновления (см. rpc/campaign.update())
        self.last_update = None
        #: Уникальность
        self.UnicImpressionLot = 1
        #: Тлько контекст, временное решение
        self.contextOnly = False
        self.retargeting = False
        
    def load(self):
        'Загружает кампанию из базы данных'
        c = app_globals.db.campaign.find_one({'guid': self.id})
        if not c:
            raise Campaign.NotFoundError(self.id)
        self.id = c['guid']
        self.title = c.get('title')
        self.social = c.get('social', False)
        self.project = c.get('project', '')
        self.yottos_partner_marker = c.get('yottosPartnerMarker', True)
        self.yottos_attractor_marker = c.get('yottosAttractorMarker', True)
        self.last_update = c.get('lastUpdate', None)
        if c.has_key('showConditions'):
            self.UnicImpressionLot = c['showConditions'].get('UnicImpressionLot', 1)
            self.contextOnly = c['showConditions'].get('contextOnly', False)
            self.retargeting = c['showConditions'].get('retargeting', False)
        else:
            self.UnicImpressionLot = 1
            self.contextOnly = False
            self.retargeting = False

    
    def restore_from_archive(self):
        'Пытается восстановить кампанию из архива. Возвращает true в случае успеха'
        c = app_globals.db.campaign.archive.find_one({'guid': self.id})
        if not c:
            return False
        self.delete()
        app_globals.db.campaign.save(c)
        app_globals.db.campaign.archive.remove({'guid': self.id}, safe=True)
    
    def save(self):
        'Сохраняет кампанию в базу данных'
        app_globals.db.campaign.update(
            {'guid': self.id},
            {'$set': {'title': self.title,
                      'social': self.social,
                      'project': self.project,
                      'yottosPartnerMarker': self.yottos_partner_marker,
                      'yottosAttractorMarker': self.yottos_attractor_marker,
                      'lastUpdate': self.last_update}},
            upsert=True, safe=True)
    
    def exists(self):
        'Возвращает ``True``, если кампания с заданным ``id`` существует'
        return (app_globals.db.campaign.find_one({'guid': self.id}) <> None)

    def delete(self):
        'Удаляет кампанию'
        app_globals.db.campaign.remove({'guid': self.id}, safe=True)
    
    def move_to_archive(self):
        'Перемещает кампанию в архив'
        c = app_globals.db.campaign.find_one({'guid': self.id})
        if not c: return
        app_globals.db.campaign.archive.remove({'guid': self.id})
        app_globals.db.campaign.archive.save(c, safe=True)
        self.delete()
