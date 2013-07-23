/****  Скрипт выводит подробную статистику кликов по предложениям или кампаниям */

var detailsLevel = 'campaigns';			// Тип отчёта, 'campaigns' или 'offers'
var dateStart = new Date(2010, 8, 14, 0, 0);	// Дата начала отчётного периода
var dateEnd = new Date(2010, 8, 15, 0, 0);	// Дата конца отчётного периода

var condition = {dt: {$gte: dateStart, $lte: dateEnd}};
condition.unique = true;
condition.cost = {$gt: 0};

/******************* Статистика по предложениям *************************/
if (detailsLevel == 'offers') {
	var result = db.clicks.group({
		cond: condition,
		key: {'title': true, cost: true}, 
		initial: {clicks: 0},
		reduce: function(o, p) {
			p.clicks += 1;
		   }
		})

	for (var title in result) {
		var row = result[title];
		print (row.title + '\t' + row.clicks + '\t' + row.cost);
	}
}


/******************* Статистика по кампаниям *************************/
if (detailsLevel == 'campaigns') {
	var result = db.clicks.group({
		cond: condition,
		key: {'offer': true, 'title': true}, 
		initial: {clicks: 0},
		reduce: function(o, p) {
			p.clicks += 1;
		   }
		})

	var campaignStats = {};
	var unknownOffers = [];

	for (var offer in result) {
		var row = result[offer];

		// Получаем id кампании, к которой относится предложение
		try {
			var campaign_id = db.offer.findOne({guid: row.offer}).campaignId;
		} catch (ex) {
			var campaign_id = '';
			unknownOffers.push(row.title);
		}

		// Получаем наименование кампании
		var campaign_title = '';
		try {
			if (campaign_id == '')
				campaign_title = 'Неопределённая кампания';
			else {
				campaign_title = db.campaign.findOne({guid: campaign_id}).title;
			}
		} catch (ex) {
			campaign_title = "Устаревшая кампания";
		}
		
		// Считаем статистику
		if (campaign_id in campaignStats) {
			campaignStats[campaign_id].clicks += row.clicks;
		} else {
			campaignStats[campaign_id] = 	{ 'title': campaign_title,
							  'clicks': row.clicks,
							  'id': campaign_id
							}
		}
		
	}
	
	// Выводим результат
	for (var id in campaignStats) {
		var row = campaignStats[id];
		print (row.title + '\t' + row.clicks);
	}

	// Неопределённые предложения
	for (var key in unknownOffers) {
//		print (unknownOffers[key]);
	}
}
