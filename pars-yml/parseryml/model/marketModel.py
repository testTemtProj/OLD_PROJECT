# This file uses following encoding: utf-8
'''
Модель магазина
'''
from parseryml.model.baseModel import Base

class MarketModel():
    errors = {
        501: [False, u'не удалось подключиться к сервису AdLoad-RPC для передачи товаров на рынок']
    }
    
    def __init__(self):
        #base_model = Base()
        self.market_collection = Base.get_market_collection()
        
    def get_states(self, stack):
        result = {}
        markets = self.market_collection.find({'id':{'$in':stack}}, {'state': 1, 'id':1})
        started = ""
        finished = ""
        delta = ""
        for market in markets:
            if 'state' in market:
                if 'started' in market['state']:
                    started = str(market['state']['started'])
                    if 'finished' in market['state']:
                        finished = str(market['state']['finished'])

                        delta = market['state']['finished'] - market['state']['started']
                        delta = {
                            'days': delta.days,
                            'sec': delta.seconds
                        }

                        del market['state']['finished']

                    del market['state']['started']

                if market['state']['state'] == 'finished':
                    status_id = 1
                elif market['state']['state'] == 'error':
                    status_id = 2
                elif market['state']['state'] == 'aborted':
                    status_id = 3
                elif market['state']['state'] == 'parsing':
                    status_id = 20
                elif market['state']['state'] == 'pending':
                    status_id = 5
                else:
                    status_id = 10
            else:
                market = {'state':'new'}
                status_id = 10

            result[market['id']] = {'state':market['state'], 'started':started, 'finished':finished, 'delta':delta, 'status_id':status_id}

        return result
    def set_state_error(self, id, code=400):
        if id>0:
            data = self.get_by_id(id)
            if self.errors[code][0]:
                data['state']['state'] = self.errors[code][0]
            data['state']['code']  = code
            data['state']['message'] = self.errors[code][1]
            self.save(data)

    def set_state_parsing(self, id):
        if id>0:
            data = self.get_by_id(id)
            data['state']['state'] = 'parsing'
            data['state']['code']  = 200
            self.save(data)

    def get_count(self, pattern=''):
        if len(pattern)>0:
            try:
                id_pattern = int(pattern)
                filter = {'id': id_pattern}
            except:
                filter = {'title': { '$regex' : pattern, '$options': 'i' }}
        else:
            filter = {}
        return self.market_collection.find(filter,{'id':1}).count()
    
    def get_all(self, skip, limit, sort_by='id', sort_dir=1, pattern='', group=''):
        fields = {'title':1, 'id':1, 'state': 1, 'urlExport': 1, 'urlMarket': 1,
                  'last_update': 1, 'time_setting': 1, 'markets':1, 'interval':1,
                  'status_id':1, 'Categories':1, 'file_date':1,'dateCreate':1}

        if sort_dir is None:
            sort_dir = 1

        if sort_by is None:
            sort_by = 'id'

        if len(pattern)>0:
            try:
                id_pattern = int(pattern)
                filter = {'id': id_pattern}
            except:
                filter = {'$or':[\
                            {'title': { '$regex': pattern, '$options': 'i' } },
                            {'urlMarket': { '$regex': pattern, '$options': 'i'} },
                            {'urlExport': { '$regex': pattern, '$options': 'i'} }
                        ]}
        else:
            filter = {}
            
        if len(group)>1:
            markets = self.market_collection.find(filter, fields).sort([(group, 1),(sort_by, sort_dir)]).skip(int(skip)).limit(int(limit));
        else:
            markets = self.market_collection.find(filter, fields).sort(sort_by, sort_dir).skip(int(skip)).limit(int(limit));

        return markets

    def get_by_id(self, id):
        market = self.market_collection.find_one({"id":int(id)})
        return market

    def save(self, data):
        if 'id' in data:
            market = self.get_by_id(data["id"])
            if market is None:
                raise NameError("Market with id: " + str(data["id"]) + " does not exist. Please don't specify the field 'ID' when inserting new market in database.")
            for key in data.keys():
                market[key] = data[key]

            self.market_collection.save(market)
            return data["id"]

        last = self.market_collection.find().sort('id', desc)[0]
        id = int(last["id"]) + 1
        data["id"] = id
        self.market_collection.insert(data)
        return id
        
    def set_time_settings(self, shop_id, data):
        self.market_collection.update({'id':int(shop_id)}, {"$set":{'time_setting':data}})
        
    def get_markts_by_ids(self, ids, filter={'_id':0,'id': 1, 'state': 1}):
        markets = []
        for x in self.market_collection.find({'id':{'$in':ids}},filter):
            markets.append(x)
        return markets
