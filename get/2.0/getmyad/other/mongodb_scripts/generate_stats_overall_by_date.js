/**
 * Считает общую статистику на заданную дату
 */
function agregateOverall(year, month, day) {
	var startDate = new Date(year, month - 1, day);
	var endDate = new Date(year, month - 1, day + 1);
	var a = db.stats_daily_adv.group({
		key: {date: true},
		cond: {
			date: {
				$gte: startDate,
				$lte: endDate
			}
		},
		reduce: function(o, p) {
			p.clicks += o.clicks || 0;
			p.clicksUnique += o.clicksUnique || 0;
			p.impressions += o.impressions || 0;
			p.totalCost += o.totalCost || 0;
		},
		initial: {clicks: 0, clicksUnique: 0, impressions: 0, totalCost: 0}
	});


	print ('Day #' + day + '\t' + a.length + '\t items');
	
	for (var i = 0; i < a.length; a++) {
		var o = a[i];
		db.stats_overall_by_date.update({
			date: o.date
		}, {
			$set: {
				clicks: o.clicks,
				clicksUnique: o.clicksUnique,
				impressions: o.impressions,
				totalCost: o.totalCost
			}
		}, {
			upsert: true
		})
	}
}


for (var d = 18;  d < 300; d++)
	agregateOverall(2010, 01, d);
