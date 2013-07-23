# This script uses following encoding: utf-8
import time, datetime
from pymongo import Connection, DESCENDING
import pyodbc

userByAdvertise = {}            # Кеш {advertise_id => userLogin}
conn = Connection()
db = conn.getmyad_db

def formatDate(d):
    return "%s-%s-%s %s:%s" % (d.year, d.day, d.month, d.hour, d.minute)


def processClick(ip, lot_guid, lot_title, dt, advertise_id):
    global userByAdvertise
    if not userByAdvertise:
        print "loading userByAdvertise"
        for x in db.Advertise.find():
            userByAdvertise[x['guid'].upper()] = x['user']['login']
    
    lot = {"guid": lot_guid, "title": lot_title}
    history = db.ip_history.find_one({"ip": ip, "clicks.lot": lot})
    
    if not history:
        cursor = db.click_cost.find({'user.login': userByAdvertise.get(advertise_id.upper()),
                                     'date': {'$lte': dt}}).sort('date', DESCENDING).limit(1)
        if cursor.count():
            cost = cursor[0]['cost']
        else:
#            print u'Не задана цена для программы',advertise_id,u'Пользователь',userByAdvertise.get(advertise_id.upper()),u'Дата',dt
            cost = 0   
    else:
        # Проверяем, не был ли именно этот клик уже записан
        for click in history['clicks']:
            if click['dt'] == dt and click['lot']['guid'] == lot_guid:
#                print "click already present: %s \t %s" % (ip, dt)
                return False
        cost = 0

    unique = False if history else True
    db.log_clicks.insert({"ip": ip,
                          "lot": lot,
                          "dt": dt,
                          "adv": advertise_id,
                          "unique": unique,
                          "cost": cost})

    db.ip_history.update({"ip": ip}, 
                         {"$push": {"clicks": {"dt": dt, "lot": lot}}}, 
                          True)

    db.stats_daily.update({'lot': lot,
                           'adv': advertise_id,
                           'date': datetime.datetime.fromordinal(dt.toordinal())},
                           {'$inc': {'clicks': 1,
                                     'clicksUnique': 1 if unique else 0,
                                     'totalCost': cost if unique else 0}
                           },
                           True)
    return True


def main():
    start = datetime.datetime(2010, 04, 19)
    end = datetime.datetime(2010, 04, 23)
    
    conn = pyodbc.connect('DRIVER={SQL Server};server=213.186.119.106;DATABASE=1gb_YottosGetMyAd;UID=web;PWD=odif8duuisdofj')
    cursor = conn.cursor()
    cursor.execute("""
                set nocount on;
                declare @lot table (id uniqueidentifier, title varchar(250))
                insert into @lot(id, title)
                select distinct LotId, Title from Lots;
                
                select ip, dateRequest, AdvertiseScriptID, LotID, title
                from [1gb_YottosStat].dbo.StatisticAds a
                inner join @lot lot on lot.id = a.LotID 
                where a.id > 140000000 and dateRequest >= '@dateStart' and dateRequest < '@dateEnd' and [Action] = 1
                order by a.id
        """.replace('@dateStart', formatDate(start)).replace('@dateEnd', formatDate(end))
        )
    
    counter = skipped = 0
    for r in cursor:
        if processClick(r.ip, r.LotID, r.title.decode('cp1251'), r.dateRequest, r.AdvertiseScriptID):
            counter += 1
        else:
            skipped += 1
    
    print "Finished. Clicks added: %s, skipped: %s" % (counter, skipped)
    
    
if __name__ == '__main__':
    print "Starting..."
    main()