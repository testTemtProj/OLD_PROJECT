/** Выводит CTR предложений за определённый период */

print ("starting...");

var dateStart = new Date(2010, 10, 18, 0, 0);	// Дата начала отчётного периода
var dateEnd = new Date(2010, 10, 19, 0, 0);		// Дата конца отчётного периода
var condition = {date: {$gte: dateStart, $lte: dateEnd}};


var result = db.stats_daily.group({
	cond: 		condition,
	key: 		{'lot.title': true},
	initial:	{'clicks': 0, 'impressions': 0},
	reduce: function (o, p) {
		p.clicks += (o.clicksUnique || 0);
		p.impressions += (o.impressions || 0);
	}
});

print ("collected " + result.length + " items");

result = result.sort(function(a,b) { return a.impressions < b.impressions });
for (var i in result) {
	var row = result[i];
	var ctr = row['clicks']? (row['clicks'] / row['impressions']) : 0;
	if (ctr)
		continue;
	print (row['lot.title'] + '\t' + row.clicks + '\t' + row.impressions + '\t' + ctr);
}
