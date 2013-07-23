# encoding: utf-8
from celery.task import task, periodic_task
from celery.schedules import crontab
import datetime
import os
import pymongo
import xmlrpclib
from statistic import GetmyadStats
from clean import GetmyadClean
from check import GetmyadCheck
from tracking import GetmyadTracking


GETMYAD_XMLRPC_HOST = 'http://getmyad.yottos.com/rpc'
GETMYAD_BANNER_XMLRPC_HOST = 'http://getmyad.yottos.com/rpc_banner'
MONGO_HOST = 'yottos.com,213.186.121.76:27018,213.186.121.199:27018'
MONGO_DATABASE = 'getmyad_db'


def _mongo_connection():
    u"""Возвращает Connection к серверу MongoDB"""
    try:
        connection = pymongo.Connection(host=MONGO_HOST)
    except pymongo.errors.AutoReconnect:
        # Пауза и повторная попытка подключиться
        from time import sleep
        sleep(1)
        connection = pymongo.Connection(host=MONGO_HOST)
    return connection

def _mongo_main_db():
    u"""Возвращает подключение к базе данных MongoDB"""
    return _mongo_connection()[MONGO_DATABASE]

def test():
    print 'Test agregate stats is start'
    elapsed_start_time = datetime.datetime.now()
    db = _mongo_main_db()
    # За сегодня
    #GetmyadStats().processMongoStats(db, datetime.date.today())
    #GetmyadStats().agregateStatDailyDomain(db, (datetime.date.today()))
    #GetmyadStats().agregateStatDailyDomain(db, (datetime.date.today() - datetime.timedelta(days=1)))
    #GetmyadStats().agregateStatDailyUser(db, (datetime.date.today()))
    #GetmyadStats().agregateStatDailyUser(db, (datetime.date.today() - datetime.timedelta(days=1)))
    #GetmyadStats().agregateStatUserSummary(db, datetime.date.today())
    print 'Test agregate stats is end %s second' % (datetime.datetime.now() - elapsed_start_time).seconds

@periodic_task(run_every=crontab(hour="*", minute=0))
def clean_ip_blacklist():
    u"""Удаляет старые записи из чёрного списка"""
    print 'Clean IP Blacklist is start'
    elapsed_start_time = datetime.datetime.now()
    db = _mongo_main_db()
    GetmyadClean().clean_ip_blacklist(db)
    print 'Clean IP Blacklist is end %s second' % (datetime.datetime.now() - elapsed_start_time).seconds


@periodic_task(run_every=crontab(hour=[0, 8, 16], minute=0))
def decline_unconfirmed_moneyout_requests():
    u"""Отклоняет заявки, которые пользователи не подтвердили в течении трёх
        дней"""
    print 'Decline unconfirmed moneyout requests is start'
    elapsed_start_time = datetime.datetime.now()
    db = _mongo_main_db()
    GetmyadClean().decline_unconfirmed_moneyout_requests(db)
    print 'Decline unconfirmed moneyout requests is end %s second' % (datetime.datetime.now() - elapsed_start_time).seconds


@periodic_task(run_every=crontab(hour="*", minute="30, 59"))
def agregate_stats():
    u"""Обработка (агрегация) статистики по дням"""
    print 'Agregate stats is start'
    elapsed_start_time = datetime.datetime.now()
    db = _mongo_main_db()
    # За сегодня
    GetmyadStats().agregate_overall_by_date(db, datetime.date.today())
    # За вчера
    GetmyadStats().agregate_overall_by_date(db, (datetime.date.today() - datetime.timedelta(days=1)))
    print 'Agregate stats is end %s second' % (datetime.datetime.now() - elapsed_start_time).seconds

@periodic_task(run_every=crontab(hour=[0,3,6,9,12,15,18], minute="30"))
def count_account():
    db = _mongo_main_db()
    # Считаем количество активных аккаунтов и сайтов за сегодня
    GetmyadStats().count_AccountsDomains_overall_by_date(db, datetime.date.today())

@periodic_task(run_every=crontab(minute=15, hour="*"))
def createOfferRating():
    u"""Создаем отдельные рейтинги для каждого рекламного блока"""
    print 'Create rating for offer is start'
    elapsed_start_time = datetime.datetime.now()
    db = _mongo_main_db()
    GetmyadStats().createOfferRating(db)
    print 'Create rating for offer is end %s second'  % (datetime.datetime.now() - elapsed_start_time).seconds


@periodic_task(run_every=crontab(minute=23, hour="*"))
def createOfferRadingForInformers():
    u"""Создаем отдельные рейтинги для каждого рекламного блока"""
    print 'Create rating for informers is start'
    elapsed_start_time = datetime.datetime.now()
    db = _mongo_main_db()
    GetmyadStats().createOfferRadingForInformers(db)
    print 'Create rating for informers is end %s second'  % (datetime.datetime.now() - elapsed_start_time).seconds

@periodic_task(run_every=crontab(hour="*", minute=40))
def updateWorkerRadingForInformers():
    u"""Обнавляем на воркере отдельные рейтинги для каждого рекламного блока"""
    print 'Update worker rating for informers is start'
    elapsed_start_time = datetime.datetime.now()
    db = _mongo_main_db()
    GetmyadStats().updateWorkerRadingForInformers(db)
    print 'Update worker rating for informers is end %s second'  % (datetime.datetime.now() - elapsed_start_time).seconds

@periodic_task(run_every=crontab(minute="0", hour="0"))
def delete_old_stats():
    u"""Удаляем старую статистику"""
    print 'Delete old data is start'
    elapsed_start_time = datetime.datetime.now()
    db = _mongo_main_db()
    GetmyadClean().delete_old_stats(db)
    print 'Delete old data is end %s second' % (datetime.datetime.now() - elapsed_start_time).seconds

@periodic_task(run_every=crontab(minute="0", hour="0"))
def delete_click_rejected():
    u"""Удаляем старые отклонённые клики"""
    print 'Delete old click rejected is start'
    elapsed_start_time = datetime.datetime.now()
    db = _mongo_main_db()
    GetmyadClean().delete_click_rejected(db)
    print 'Delete old click rejected is end %s second' % (datetime.datetime.now() - elapsed_start_time).seconds
        
@periodic_task(run_every=crontab(minute=10, hour=0))
def delete_old_rating_stats():
    u"""Удаляем старую статистику для рейтингов"""
    print 'Delete old rating data is start'
    elapsed_start_time = datetime.datetime.now()
    db = _mongo_main_db()
    GetmyadClean().delete_old_rating_stats(db)
    print 'Delete old rating data is end %s second' % (datetime.datetime.now() - elapsed_start_time).seconds

@periodic_task(run_every=crontab(minute="*/10", hour="*"))
def check_outdated_campaigns():
    u"""Иногда AdLoad не оповещает GetMyAd об остановке кампании.
        Данная задача проверяет, не произошло ли за последнее время несколько
        таких ошибок и, если произошло, обновляет кампанию."""
    print 'Check outdate campaigns is start'
    elapsed_start_time = datetime.datetime.now()
    db = _mongo_main_db()
    rpc = xmlrpclib.ServerProxy(GETMYAD_XMLRPC_HOST)
    GetmyadCheck().check_outdated_campaigns(db, rpc)
    print 'Check outdate campaigns is end %s second' % (datetime.datetime.now() - elapsed_start_time).seconds

@periodic_task(run_every=crontab(minute="*/10", hour="*"))
def check_banner_budget():
    print 'Check outdate banner is start'
    elapsed_start_time = datetime.datetime.now()
    db = _mongo_main_db()
    rpc = xmlrpclib.ServerProxy(GETMYAD_BANNER_XMLRPC_HOST)
    GetmyadCheck().check_banner_budget(db, rpc)
    print 'Check outdate banner is end %s second' % (datetime.datetime.now() - elapsed_start_time).seconds

@periodic_task(run_every=crontab(hour="*", minute=0))
def importBadClicksFromMongo():
    u"""Обработка отклоненных кликов из mongo"""
    elapsed_start_time = datetime.datetime.now()
    print 'Count bad cliks to stats_daily is start'
    db = _mongo_main_db()
    GetmyadStats().importBadClicksFromMongo(db)
    print 'Count badcliks elapsed %s second' % (datetime.datetime.now() - elapsed_start_time).seconds

@periodic_task(run_every=crontab(hour="*", minute="*/20"))
def stats_daily_update_clicks():
    u"""Обработка кликов из mongo"""
    elapsed_start_time = datetime.datetime.now()
    print 'Count clicks to stats_daily is start'
    db = _mongo_main_db()
    GetmyadStats().importClicksFromMongo(db)
    print 'Count cliks elapsed %s second' % (datetime.datetime.now() - elapsed_start_time).seconds

@periodic_task(run_every=crontab(hour="*", minute="25, 50"))
def stats_daily_adv_update():
    u"""Обработка (агрегация) статистики"""
    db = _mongo_main_db()
    # За сегодня
    print 'Update stats_daily_adv is start'
    elapsed_start_time = datetime.datetime.now()
    GetmyadStats().processMongoStats(db, datetime.date.today())
    print 'Update stats_daily_adv elapsed %s second' % (datetime.datetime.now() - elapsed_start_time).seconds
    print 'Agregate stats Domain is start'
    elapsed_start_time = datetime.datetime.now()
    GetmyadStats().agregateStatDailyDomain(db, datetime.date.today())
    print 'Agregate stats Domain is end %s second' % (datetime.datetime.now() - elapsed_start_time).seconds
    print 'Agregate User stats is start'
    elapsed_start_time = datetime.datetime.now()
    GetmyadStats().agregateStatDailyUser(db, datetime.date.today())
    print 'Agregate User stats is end %s second' % (datetime.datetime.now() - elapsed_start_time).seconds
    print 'Agregate Daily stats is start'
    elapsed_start_time = datetime.datetime.now()
    GetmyadStats().agregateStatDailyAll(db, datetime.date.today())
    print 'Agregate Daily stats is end %s second' % (datetime.datetime.now() - elapsed_start_time).seconds
    # За вчера
    print 'Update stats_daily_adv is start'
    elapsed_start_time = datetime.datetime.now()
    GetmyadStats().processMongoStats(db, (datetime.date.today() - datetime.timedelta(days=1)))
    print 'Update stats_daily_adv elapsed %s second' % (datetime.datetime.now() - elapsed_start_time).seconds
    print 'Agregate stats Domain is start'
    elapsed_start_time = datetime.datetime.now()
    GetmyadStats().agregateStatDailyDomain(db, (datetime.date.today() - datetime.timedelta(days=1)))
    print 'Agregate stats Domain is end %s second' % (datetime.datetime.now() - elapsed_start_time).seconds
    print 'Agregate User stats is start'
    elapsed_start_time = datetime.datetime.now()
    GetmyadStats().agregateStatDailyUser(db, (datetime.date.today() - datetime.timedelta(days=1)))
    print 'Agregate User stats is end %s second' % (datetime.datetime.now() - elapsed_start_time).seconds
    print 'Agregate Daily stats is start'
    elapsed_start_time = datetime.datetime.now()
    GetmyadStats().agregateStatDailyAll(db, (datetime.date.today() - datetime.timedelta(days=1)))
    print 'Agregate Daily stats is end %s second' % (datetime.datetime.now() - elapsed_start_time).seconds

    print 'Agregate UserSumary stats is start'
    elapsed_start_time = datetime.datetime.now()
    GetmyadStats().agregateStatUserSummary(db, datetime.date.today())
    print 'Agregate UserSumary stats is end %s second' % (datetime.datetime.now() - elapsed_start_time).seconds

@periodic_task(run_every=crontab(minute=1, hour="0"))
def agregateBannerStatsDailyAdv():
    u"""Обработка (агрегация) статистики банеров по дням"""
    print 'Agregate Banner stats is start'
    elapsed_start_time = datetime.datetime.now()
    db = _mongo_main_db()
    # За вчера
    GetmyadStats().agregateBannerStatsDailyAdv(db, (datetime.date.today() - datetime.timedelta(days=1)))
    # За позавчера
    GetmyadStats().agregateBannerStatsDailyAdv(db, (datetime.date.today() - datetime.timedelta(days=2)))
    print 'Agregate Banner stats is end %s second' % (datetime.datetime.now() - elapsed_start_time).seconds

@periodic_task(run_every=crontab(minute="0", hour="23"))
def create_xsl_report():
    u"""Создаёт xls отчёты"""
    print 'Create XLS report'
    elapsed_start_time = datetime.datetime.now()
    db = _mongo_main_db()
    GetmyadStats().createCatigoriesDomainReport(db, (datetime.date.today() - datetime.timedelta(days=1)))
    print 'Create XLS report is end %s second' % (datetime.datetime.now() - elapsed_start_time).seconds

@periodic_task(run_every=crontab(minute="*/10", hour="*"))
def retargeting():
    u"""
        """
    print 'Retargeting analytyc is start'
    elapsed_start_time = datetime.datetime.now()
    db = _mongo_main_db()
    redisRetargeting = [('srv-2.yottos.com',6385),('srv-3.yottos.com',6385)]
    GetmyadTracking().trackingAnalytic(db, redisRetargeting)
    print 'Retargeting analytyc is end %s second' % (datetime.datetime.now() - elapsed_start_time).seconds
