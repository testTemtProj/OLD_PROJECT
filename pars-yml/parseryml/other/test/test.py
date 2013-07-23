import pymongo as p

db = p.Connection(['10.0.0.8:27018', '10.0.0.8:27017', '10.0.0.8:27019']).parser

if __name__ == '__main__':
	file = open('models.txt','a')
	for x in db.Model.find().sort('name',1):
		file.write(x['name'].encode('UTF-8')+'\n')
	file.close()
