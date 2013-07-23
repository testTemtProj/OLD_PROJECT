/** Скрипт подготавливает базу данных с регионами */


var regions = {
"Cherkas'ka Oblast'": "Черкассы",
"Chernihivs'ka Oblast'": "Чернигов",
"Chernivets'ka Oblast'": "Черновцы",
"Dnipropetrovs'ka Oblast'": "Днепропетровск",
"Donets'ka Oblast'": "Донецк",
"Ivano-Frankivs'ka Oblast'": "Ивано-Франковск",
"Kharkivs'ka Oblast'": "Харьков",
"Khersons'ka Oblast'": "Херсон",
"Khmel'nyts'ka Oblast'": "Хмельницкий",
"Kirovohrads'ka Oblast'": "Кировоград",
"Krym": "Крым",
"Kyyivs'ka Oblast'": "Киев",
"L'vivs'ka Oblast'": "Львов",
"Luhans'ka Oblast'": "Луганск",
"Mykolayivs'ka Oblast'": "Николаев",
"Odes'ka Oblast'": "Одесса",
"Poltavs'ka Oblast'": "Полтава",
"Rivnens'ka Oblast'": "Ровно",
"Sevastopol'": "Севастополь",
"Sums'ka Oblast'": "Сумы",
"Ternopil's'ka Oblast'": "Тернополь",
"Vinnyts'ka Oblast'": "Винница",
"Volyns'ka Oblast'": "Луцк",
"Zakarpats'ka Oblast'": "Закарпатье",
"Zaporiz'ka Oblast'": "Запорожье",
"Zhytomyrs'ka Oblast'": "Житомир",
}

for (var key in regions) {
	var rus = regions[key];
	db.geo.regions.update( {'region': key}, {$set: {'ru': rus}}, true );
}
