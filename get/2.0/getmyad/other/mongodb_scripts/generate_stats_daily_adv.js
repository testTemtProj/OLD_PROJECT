/*  Создаёт таблицу с суммарной статистикой по каждой выгрузке отдельно.
	На входе использует таблицу stats_daily.
	На выходе таблица stats_daily_adv.
*/

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
