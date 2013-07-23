# This Python file uses the following encoding: utf-8
import time, datetime
from pymongo import Connection, DESCENDING
import pyodbc
from paste.util.import_string import try_import_module

conn = Connection()
db = conn.getmyad_db

userByAdvertise = {}            # Кеш {advertise_id => userLogin}


def processClick(ip, lot_guid, lot_title, dt, advertise_id):
    global userByAdvertise
    if not userByAdvertise:
        print "loading userByAdvertise"
        for x in db.Advertise.find():
            userByAdvertise[x['guid'].upper()] = x['user']['login']
    
    lot = {"guid": lot_guid, "title": lot_title}
    unique = ( db.ip_history.find({"ip": ip, "clicks.lot": lot}).count() == 0)
    if unique:
        cursor = db.click_cost.find({'user.login': userByAdvertise.get(advertise_id.upper()),
                                     'date': {'$lte': dt}}).sort('date', DESCENDING).limit(1)
        if cursor.count():
            cost = cursor[0]['cost']
        else:
#            print u'Не задана цена для программы',advertise_id,u'Пользователь',userByAdvertise.get(advertise_id.upper()),u'Дата',dt
            cost = 0   
    else:
        cost = 0

    db.log_clicks.insert({"ip": ip,
                          "lot": lot,
                          "dt": dt,
                          "adv": advertise_id,
                          "unique": unique,
                          "cost": cost})

    db.ip_history.update({"ip": ip}, 
                         {"$push": {"clicks": {"dt": dt, "lot": lot}}}, 
                          True)

    db.stats_daily.update({'lot.guid': lot_guid,
                           'lot.title': lot_title,
                           'adv': advertise_id,
                           'date': datetime.datetime.fromordinal(dt.toordinal())},
                           {'$inc': {'clicks': 1,
                                     'clicksUnique': 1 if unique else 0,
                                     'totalCost': cost if unique else 0}
                           },
                           True)


def importClicksFromDatabase():
    global db
    start = None
    try:
        start = db.config.find_one({'key': 'clicks last date'})['value']
    except:
        pass
    if not isinstance(start, datetime.datetime):
        start = datetime.datetime(2000,01,01)
        
    now = datetime.datetime.now()
    end = datetime.datetime(now.year, now.month, now.day, now.hour)     # Round to 1 hour
    
    def formatDate(d):
        return "%s-%s-%s %s:%s" % (d.year, d.day, d.month, d.hour, d.minute)
    
    print "Processing clicks from %s to %s" % (start, end)

    
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
where a.id > 170000000 and dateRequest >= '@dateStart' and dateRequest < '@dateEnd' and [Action] = 1
order by a.id
    """.replace('@dateStart', formatDate(start)).replace('@dateEnd', formatDate(end))
    )
    
    for r in cursor:
        processClick(r.ip, r.LotID, r.title.decode('cp1251'), r.dateRequest, r.AdvertiseScriptID)
        
    db.config.update({'key': 'clicks last date'}, {'$set': {'value': end}}, True)



def importClicks(filename):
    global db
    f = open(filename, 'r')
    f.readline()                # skip first line
    i = 0
    start = time.time()
    for row in f:
        t = row.split('\t')
        if len(t) < 5:
            continue
        
        dt = datetime.datetime.fromtimestamp(time.mktime(time.strptime(t[1][:-4], '%Y-%m-%d %H:%M:%S')))
        ip = t[0]
        lot_guid = t[3]
        lot_title = t[4].rstrip('\r\n')
        advertise_id = t[2]
        processClick(ip, lot_guid, lot_title, dt, advertise_id)
        if i % 10000 == 0:
            print i, "time:", time.time() - start, "secs."
            start = time.time()
        i += 1
    f.close()


#def importImpressions(filename):
#    global db
#    f = open(filename, 'r')
#    f.readline()                # skip first line
#    i = 0
#    buffer = {}
#    start = time.time()
#    for row in f:
#        t = row.split('\t')
#        if len(t) < 5:
#            continue
#        
#        dt = datetime.datetime.fromtimestamp(time.mktime(time.strptime(t[1][:10], '%Y-%m-%d')))
#        
#        key = (t[3], t[4].rstrip('\r\n'), t[2], dt)
#        if not buffer.has_key(key):
#            buffer[key] = 1
#        else:
#            buffer[key] += 1 
#        i += 1
#        if i % 50000 == 0:
#            print i, 'buffer has',len(buffer),'keys, time:',time.time() - start, "secs"
#        
#    for key,value in buffer.items():
#        db.stats_daily.update({'lot': {'guid': key[0], 'title': key[1]},
#                               'adv': key[2],
#                               'date': key[3]},
#                               {'$inc': {'impressions': value}},
#                               True)
#        
#    print "imported",i,"items in", time.time() - start, "secs"


def importImpressionsFromDatabase():
    global db
    start = None
    try:
        start = db.config.find_one({'key': 'impressions last date'})['value']
    except:
        pass
    if not isinstance(start, datetime.datetime):
        start = datetime.datetime(2000,01,01)
        
    now = datetime.datetime.now()
    end = datetime.datetime(now.year, now.month, now.day, now.hour)     # Round to 1 hour
    
    def formatDate(d):
        return "%s-%s-%s %s:%s" % (d.year, d.day, d.month, d.hour, d.minute)
    
    print "Processing impressions from %s to %s" % (start, end)

    
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
where a.id > 170000000 and dateRequest >= '@dateStart' and dateRequest < '@dateEnd' and [Action] = 0
    """.replace('@dateStart', formatDate(start)).replace('@dateEnd', formatDate(end))
    )
    
    buffer = {}
    for r in cursor:
        n = r.dateRequest
        dt = datetime.datetime(n.year, n.month, n.day)
        key = (r.LotID, r.title.decode('cp1251'), r.AdvertiseScriptID, dt)
        if buffer.has_key(key):
            buffer[key] += 1
        else:
            buffer[key] = 1
            
    print 'buffer has',len(buffer),'keys'
    db.reset_error_history()
    for key,value in buffer.items():
        db.stats_daily.update({'lot.guid': key[0],
                               'lot.title': key[1],
                               'adv': key[2],
                               'date': key[3]},
                               {'$inc': {'impressions': value}},
                               True)
    if db.previous_error():
        print "Database error", db.previous_error() 

    db.reset_error_history()
    print "update end time to", end        
    db.config.update({'key': 'impressions last date'}, {'$set': {'value': end}}, True)
    if db.previous_error():
        print "Database error", db.previous_error() 


def processMongoStats():
    """ Обновляет промежуточную статистику в mongo"""
    db.eval('''
        function() {
            var startDate = new Date();
            startDate.setDate((new Date).getDate() - 2);
            
            var a = db.stats_daily.group({
                    key: {adv:true, date:true},
                    cond: {date: {$gt: startDate}},
                    reduce: function(obj,prev){
                                                prev.totalCost += obj.totalCost || 0;
                                                prev.impressions += obj.impressions || 0;
                                                prev.clicks += obj.clicks || 0;
                                                prev.clicksUnique += obj.clicksUnique || 0;
                                            },
                    initial: {totalCost: 0,
                              impressions:0,
                              clicks:0,
                              clicksUnique:0}})
                              
            for (var i=0; i<a.length; i++) {
                var o = a[i];
                db.stats_daily_adv.update(
                    {adv: o.adv, date: o.date},
                    {$set: {totalCost: o.totalCost,
                            impressions: o.impressions,
                            clicks: o.clicks,
                            clicksUnique: o.clicksUnique,
                            totalCost: o.totalCost
                            }},
                    {upsert: true})
            }
            
            db.stats_daily_adv.ensureIndex({adv:1})
        }
        ''')
    


if __name__ == '__main__':
    importClicksFromDatabase()
    importImpressionsFromDatabase()
    processMongoStats()