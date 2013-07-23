# encoding: utf-8
from pymongo import Connection, DESCENDING
import datetime
import pymongo
import xmlrpclib

class GetmyadCheck():

    def check_outdated_campaigns(self, db, rpc):
        ''' Иногда AdLoad не оповещает GetMyAd об остановке кампании, об отработке
            парсера и т.д. Это приводит к тому, что кампания продолжает крутиться
            в GetMyAd, но клики не засчитываются и записываются в clicks.error.
            Данная задача проверяет, не произошло ли за последнее время несколько
            таких ошибок и, если произошло, обновляет кампанию. '''

        WATCH_LAST_N_MINUTES = 30   # Смотрим лог за последние N минут
        ALLOWED_ERRORS = 0          # Допустимое количество ошибок на одну кампанию

        # Смотрим лог ошибок, начиная с конца
        c = db['clicks.error'].find().sort('$natural', pymongo.DESCENDING)
        now = datetime.datetime.now()
        errors_per_campaign = {}
        for item in c:
            if (now - item['dt']).seconds > 15 * 60:
                break
            campaign = item.get('campaignId')
            errors_per_campaign.setdefault(campaign, 0)
            errors_per_campaign[campaign] += 1

        # Обновляем кампании, у которых превышен лимит ошибок
        outdated_campaigns = [c for c, e in errors_per_campaign.items()
                                         if e > ALLOWED_ERRORS]
        if outdated_campaigns:
            print "outdated_campaigns = %s" % repr(outdated_campaigns)
        else:
            print "No outdated campaigns"
        for campaign in outdated_campaigns:
            if campaign is None:
                print "Unknown campaign, skipped"
                continue
            rpc.campaign.update(campaign)

    def check_banner_budget(self, db, banner_rpc):
        banner_cost = {}
        banner_budget = {}
        cur = db.banner.offer.find()
        for item in cur:
            banner_cost[item['guid']] = item['imp_cost']
            banner_budget[item['guid']] = item['budget']
        date = datetime.datetime.now()
        date = datetime.datetime(date.year, date.month, date.day, 0, 0)
        banner = db.banner.stats_daily.group(
                key = ['guid','campaignId'],
                condition = {'date': {'$gte': date}},
                reduce = '''function(obj,prev) {
                        prev.banner_impressions += obj.banner_impressions;
                }''',
                initial = {'banner_impressions': 0}
                )
        for item in banner:
            if (((banner_cost[item['guid']]/1000) * item['banner_impressions']) >= banner_budget[item['guid']]):
                if banner_rpc.campaign.details(item['campaignId'])['status'] != 'not_found':
                    print 'Stop Banner Campaign id=%s' %item['campaignId']
                    banner_rpc.campaign.stop(item['campaignId'])            
