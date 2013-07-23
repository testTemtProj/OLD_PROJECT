from pymongo import Connection
from datetime import datetime
conn = Connection()
db = conn.getmyad_db


users = {'mycityuacom': 0.05,
         'joinua': 0.06,
         'mostua': 0.06,
         'meteoprog': 0.08}

dateEnd = datetime(2010, 01, 24, 22, 41)
#dateEnd = datetime.now()


for login, rate in users.items():
    for ad in db.Advertise.find({'user.login': login}):
        db.log_clicks.update({'adv': ad['guid'], 'dt': {'$lt': dateEnd}, 'unique': True},
                              {'$set': {'cost': rate}},
                              multi=True, safe=True)
        print login, rate, ad['title']


buffer = {}
for r in db.log_clicks.find():
    dt = datetime(r['dt'].year, r['dt'].month, r['dt'].day)
    key = (r['lot']['guid'], r['lot']['title'], r['adv'], dt)
    if buffer.has_key(key):
        buffer[key] += r['cost']
    else:
        buffer[key] = r['cost']
        
db.reset_error_history()
for key,value in buffer.items():
    db.stats_daily.update({'lot': {'guid': key[0], 'title': key[1]},
                           'adv': key[2],
                           'date': key[3]},
                           {'$set': {'totalCost': value}})
if db.previous_error():
    print "Database error", db.previous_error() 

                   
                   
#> db.log_clicks.find({adv: "49A37671-D505-4B07-8BCA-0B3F65A99B73", unique: true, dt: {$lte: new Date(2010,00,24, 22, 41)}}).count()
