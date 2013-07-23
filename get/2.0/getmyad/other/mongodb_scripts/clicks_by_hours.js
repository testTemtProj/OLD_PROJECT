/** Выводит статистику кликов, разбитую по часам */
var day = 15;
var month = 9;
var year = 2010;

var total = 0;
for (var hour = 3; hour < 27; hour++) {
  var dt1 = new Date(year, month, day, hour, 0);
  var dt2 = new Date(year, month, day, hour + 1, 0);
  var clicks = db.clicks.find({dt: {$gte:  dt1, $lte: dt2}}).count();
   print (hour -3 + '\t' + clicks );
   total += clicks;
}

print ('-------');
print ('TOTAL:\t' + total);
