// Скрипт проверяет состояние локальной базы данных getmyad (которая используется worker'ами)
// При необходимости восстанавливает

if (!db.log.impressions.validate().valid || !db.log.impressions.stats().capped) {
	print ("Database broken, recreating collections");	
	db.log.impressions.drop();
	db.createCollection('log.impressions', {size: 250000000, capped: true, max: 1000000});
	db.log.impressions.ensureIndex({'token': 1});
}
