import pymongo as p
import time
from datetime import datetime as dt

CONNECT_TO_MONGO = ['10.0.0.8:27018', '10.0.0.8:27017', '10.0.0.8:27019']

if __name__ == '__main__':
	db = p.Connection(CONNECT_TO_MONGO).rynok
	vendors = []
	for x in db.Yottos_venders.find():
		vendors.append(x['name'])
	id = 0
	t1 = time.time()
	print 'Start'
	for x in db.Offers.find():
		try:
			print x['vendor']
			if x['vendor'] not in vendors:
				vendors.append(x['vendor'])
				tmp = {}
				tmp['id'] = id
				tmp['name'] = x['vendor']
				db.Yottos_venders.insert(tmp)
				id += 1
		except:
			pass
	
	t2 = time.time()
	print "Done in time: " + str(t2-t1) + " sec"
