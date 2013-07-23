#include "InformerTemplate.h"

/** Шаблон информера с тизерами со следующими подстановками (существовавший шаблон):

    %1%	    CSS
    %2%	    JSON для initads (предложения, которые должны показаться на первой
	    странице)
    %3%	    количество товаров на странице
    %4%	    ссылка на скрипт получения следующей порции предложений в json,
	    к ней будут добавляться дополнительные параметры.
*/
bool InformerTemplate::initTeasersTemplate()
{
	if (teasersTemplate!="")
	{
		return true;
	}

	teasersTemplate = 
		"<html><head>"
		"<META http-equiv=\"Content-Type\" content=\"text/html; charset=utf-8\"><meta name=\"robots\" content=\"nofollow\" />\n"
		"<style type=\"text/css\">html, body {padding: 0; margin: 0; border: 0;}</style>\n"
		" %1% \n"
		"</head> \n"
		"<body> \n"
		"  <div id=\"mainContainer\"> \n"
		"  \n"
		"  	<div id='adsContainer'></div> \n"
		"              <div id=\"adInfo\"><a href=\"http://yottos.ru/Рекламные_программы\" target=\"_blank\" title=\"Реклама от Yottos\"></a></div> \n"
		"              <a href='javascript:prev();'> <div class=\"navr\" id='nav_r' style=\"display:none\" onmouseover=\"change('b');\" onmouseout=\"change1('b');\" > <div id=\"leftArrow\" style=\"width:12;height:16px;\"> \n"
		"  <div class=\"b1\" style=\"left:3px;top:7px;\"></div><div class=\"b1\" style=\"left:3px;top:8px;\"></div><div class=\"b1\" style=\"left:4px;top:6px;\"></div><div class=\"b1\" style=\"left:4px;top:7px;\"></div><div class=\"b1\" style=\"left:4px;top:8px;\"></div><div class=\"b1\" style=\"left:4px;top:9px;\"></div><div class=\"b1\" style=\"left:5px;top:5px;\"></div><div class=\"b1\" style=\"left:5px;top:6px;\"></div><div class=\"b1\" style=\"left:5px;top:7px;\"></div><div class=\"b1\" style=\"left:5px;top:8px;\"></div><div class=\"b1\" style=\"left:5px;top:9px;\"></div><div class=\"b1\" style=\"left:5px;top:10px;\"></div><div class=\"b1\" style=\"left:6px;top:4px;\"></div><div class=\"b1\" style=\"left:6px;top:5px;\"></div><div class=\"b1\" style=\"left:6px;top:6px;\"></div><div class=\"b1\" style=\"left:6px;top:9px;\"></div><div class=\"b1\" style=\"left:6px;top:10px;\"></div><div class=\"b1\" style=\"left:6px;top:11px;\"></div><div class=\"b1\" style=\"left:7px;top:3px;\"></div><div class=\"b1\" style=\"left:7px;top:4px;\"></div><div class=\"b1\" style=\"left:7px;top:5px;\"></div><div class=\"b1\" style=\"left:7px;top:10px;\"></div><div class=\"b1\" style=\"left:7px;top:11px;\"></div><div class=\"b1\" style=\"left:7px;top:12px;\"></div><div class=\"b1\" style=\"left:8px;top:2px;\"></div><div class=\"b1\" style=\"left:8px;top:3px;\"></div><div class=\"b1\" style=\"left:8px;top:4px;\"></div><div class=\"b1\" style=\"left:8px;top:11px;\"></div><div class=\"b1\" style=\"left:8px;top:12px;\"></div><div class=\"b1\" style=\"left:8px;top:13px;\"></div> \n"
		"  <div class=\"b\" style=\"left:0px;top:7px;\"></div><div class=\"b\" style=\"left:0px;top:8px;\"></div><div class=\"b\" style=\"left:1px;top:6px;\"></div><div class=\"b\" style=\"left:1px;top:7px;\"></div><div class=\"b\" style=\"left:1px;top:8px;\"></div><div class=\"b\" style=\"left:1px;top:9px;\"></div><div class=\"b\" style=\"left:2px;top:5px;\"></div><div class=\"b\" style=\"left:2px;top:6px;\"></div><div class=\"b\" style=\"left:2px;top:7px;\"></div><div class=\"b\" style=\"left:2px;top:8px;\"></div><div class=\"b\" style=\"left:2px;top:9px;\"></div><div class=\"b\" style=\"left:2px;top:10px;\"></div><div class=\"b\" style=\"left:3px;top:4px;\"></div><div class=\"b\" style=\"left:3px;top:5px;\"></div><div class=\"b\" style=\"left:3px;top:6px;\"></div><div class=\"b\" style=\"left:3px;top:9px;\"></div><div class=\"b\" style=\"left:3px;top:10px;\"></div><div class=\"b\" style=\"left:3px;top:11px;\"></div><div class=\"b\" style=\"left:4px;top:3px;\"></div><div class=\"b\" style=\"left:4px;top:4px;\"></div><div class=\"b\" style=\"left:4px;top:5px;\"></div><div class=\"b\" style=\"left:4px;top:10px;\"></div><div class=\"b\" style=\"left:4px;top:11px;\"></div><div class=\"b\" style=\"left:4px;top:12px;\"></div><div class=\"b\" style=\"left:5px;top:2px;\"></div><div class=\"b\" style=\"left:5px;top:3px;\"></div><div class=\"b\" style=\"left:5px;top:4px;\"></div><div class=\"b\" style=\"left:5px;top:11px;\"></div><div class=\"b\" style=\"left:5px;top:12px;\"></div><div class=\"b\" style=\"left:5px;top:13px;\"></div><div class=\"b\" style=\"left:6px;top:1px;\"></div><div class=\"b\" style=\"left:6px;top:2px;\"></div><div class=\"b\" style=\"left:6px;top:3px;\"></div><div class=\"b\" style=\"left:6px;top:7px;\"></div><div class=\"b\" style=\"left:6px;top:8px;\"></div><div class=\"b\" style=\"left:6px;top:12px;\"></div><div class=\"b\" style=\"left:6px;top:13px;\"></div><div class=\"b\" style=\"left:6px;top:14px;\"></div><div class=\"b\" style=\"left:7px;top:0px;\"></div><div class=\"b\" style=\"left:7px;top:1px;\"></div><div class=\"b\" style=\"left:7px;top:2px;\"></div><div class=\"b\" style=\"left:7px;top:6px;\"></div><div class=\"b\" style=\"left:7px;top:7px;\"></div><div class=\"b\" style=\"left:7px;top:8px;\"></div><div class=\"b\" style=\"left:7px;top:9px;\"></div><div class=\"b\" style=\"left:7px;top:13px;\"></div><div class=\"b\" style=\"left:7px;top:14px;\"></div><div class=\"b\" style=\"left:7px;top:15px;\"></div><div class=\"b\" style=\"left:8px;top:0px;\"></div><div class=\"b\" style=\"left:8px;top:1px;\"></div><div class=\"b\" style=\"left:8px;top:5px;\"></div><div class=\"b\" style=\"left:8px;top:6px;\"></div><div class=\"b\" style=\"left:8px;top:7px;\"></div><div class=\"b\" style=\"left:8px;top:8px;\"></div><div class=\"b\" style=\"left:8px;top:9px;\"></div><div class=\"b\" style=\"left:8px;top:10px;\"></div><div class=\"b\" style=\"left:8px;top:14px;\"></div><div class=\"b\" style=\"left:8px;top:15px;\"></div><div class=\"b\" style=\"left:9px;top:0px;\"></div><div class=\"b\" style=\"left:9px;top:1px;\"></div><div class=\"b\" style=\"left:9px;top:2px;\"></div><div class=\"b\" style=\"left:9px;top:3px;\"></div><div class=\"b\" style=\"left:9px;top:4px;\"></div><div class=\"b\" style=\"left:9px;top:5px;\"></div><div class=\"b\" style=\"left:9px;top:6px;\"></div><div class=\"b\" style=\"left:9px;top:7px;\"></div><div class=\"b\" style=\"left:9px;top:8px;\"></div><div class=\"b\" style=\"left:9px;top:9px;\"></div><div class=\"b\" style=\"left:9px;top:10px;\"></div><div class=\"b\" style=\"left:9px;top:11px;\"></div><div class=\"b\" style=\"left:9px;top:12px;\"></div><div class=\"b\" style=\"left:9px;top:13px;\"></div><div class=\"b\" style=\"left:9px;top:14px;\"></div><div class=\"b\" style=\"left:9px;top:15px;\"></div><div class=\"b\" style=\"left:10px;top:0px;\"></div><div class=\"b\" style=\"left:10px;top:1px;\"></div><div class=\"b\" style=\"left:10px;top:2px;\"></div><div class=\"b\" style=\"left:10px;top:3px;\"></div><div class=\"b\" style=\"left:10px;top:4px;\"></div><div class=\"b\" style=\"left:10px;top:5px;\"></div><div class=\"b\" style=\"left:10px;top:6px;\"></div><div class=\"b\" style=\"left:10px;top:7px;\"></div><div class=\"b\" style=\"left:10px;top:8px;\"></div><div class=\"b\" style=\"left:10px;top:9px;\"></div><div class=\"b\" style=\"left:10px;top:10px;\"></div><div class=\"b\" style=\"left:10px;top:11px;\"></div><div class=\"b\" style=\"left:10px;top:12px;\"></div><div class=\"b\" style=\"left:10px;top:13px;\"></div><div class=\"b\" style=\"left:10px;top:14px;\"></div><div class=\"b\" style=\"left:10px;top:15px;\"></div> \n"
		"               </div>  </div> </a> \n"
		"  \n"
		"  \n"
		"             <a href='javascript:next();'> <div class=\"nav\" id=\"nav_l\" onmouseover=\"change('c');\" onmouseout=\"change1('c');\" > <div id=\"rightArrow\" style=\"width:12;height:16px;\"> \n"
		"  <div class=\"c1\" style=\"left:2px;top:2px;\"></div><div class=\"c1\" style=\"left:2px;top:3px;\"></div><div class=\"c1\" style=\"left:2px;top:4px;\"></div><div class=\"c1\" style=\"left:2px;top:11px;\"></div><div class=\"c1\" style=\"left:2px;top:12px;\"></div><div class=\"c1\" style=\"left:2px;top:13px;\"></div><div class=\"c1\" style=\"left:3px;top:3px;\"></div><div class=\"c1\" style=\"left:3px;top:4px;\"></div><div class=\"c1\" style=\"left:3px;top:5px;\"></div><div class=\"c1\" style=\"left:3px;top:10px;\"></div><div class=\"c1\" style=\"left:3px;top:11px;\"></div><div class=\"c1\" style=\"left:3px;top:12px;\"></div><div class=\"c1\" style=\"left:4px;top:4px;\"></div><div class=\"c1\" style=\"left:4px;top:5px;\"></div><div class=\"c1\" style=\"left:4px;top:6px;\"></div><div class=\"c1\" style=\"left:4px;top:9px;\"></div><div class=\"c1\" style=\"left:4px;top:10px;\"></div><div class=\"c1\" style=\"left:4px;top:11px;\"></div><div class=\"c1\" style=\"left:5px;top:5px;\"></div><div class=\"c1\" style=\"left:5px;top:6px;\"></div><div class=\"c1\" style=\"left:5px;top:7px;\"></div><div class=\"c1\" style=\"left:5px;top:8px;\"></div><div class=\"c1\" style=\"left:5px;top:9px;\"></div><div class=\"c1\" style=\"left:5px;top:10px;\"></div><div class=\"c1\" style=\"left:6px;top:6px;\"></div><div class=\"c1\" style=\"left:6px;top:7px;\"></div><div class=\"c1\" style=\"left:6px;top:8px;\"></div><div class=\"c1\" style=\"left:6px;top:9px;\"></div><div class=\"c1\" style=\"left:7px;top:7px;\"></div><div class=\"c1\" style=\"left:7px;top:8px;\"></div> \n"
		"  <div class=\"c\" style=\"left:0px;top:0px;\"></div><div class=\"c\" style=\"left:0px;top:1px;\"></div><div class=\"c\" style=\"left:0px;top:2px;\"></div><div class=\"c\" style=\"left:0px;top:3px;\"></div><div class=\"c\" style=\"left:0px;top:4px;\"></div><div class=\"c\" style=\"left:0px;top:5px;\"></div><div class=\"c\" style=\"left:0px;top:6px;\"></div><div class=\"c\" style=\"left:0px;top:7px;\"></div><div class=\"c\" style=\"left:0px;top:8px;\"></div><div class=\"c\" style=\"left:0px;top:9px;\"></div><div class=\"c\" style=\"left:0px;top:10px;\"></div><div class=\"c\" style=\"left:0px;top:11px;\"></div><div class=\"c\" style=\"left:0px;top:12px;\"></div><div class=\"c\" style=\"left:0px;top:13px;\"></div><div class=\"c\" style=\"left:0px;top:14px;\"></div><div class=\"c\" style=\"left:0px;top:15px;\"></div><div class=\"c\" style=\"left:1px;top:0px;\"></div><div class=\"c\" style=\"left:1px;top:1px;\"></div><div class=\"c\" style=\"left:1px;top:2px;\"></div><div class=\"c\" style=\"left:1px;top:3px;\"></div><div class=\"c\" style=\"left:1px;top:4px;\"></div><div class=\"c\" style=\"left:1px;top:5px;\"></div><div class=\"c\" style=\"left:1px;top:6px;\"></div><div class=\"c\" style=\"left:1px;top:7px;\"></div><div class=\"c\" style=\"left:1px;top:8px;\"></div><div class=\"c\" style=\"left:1px;top:9px;\"></div><div class=\"c\" style=\"left:1px;top:10px;\"></div><div class=\"c\" style=\"left:1px;top:11px;\"></div><div class=\"c\" style=\"left:1px;top:12px;\"></div><div class=\"c\" style=\"left:1px;top:13px;\"></div><div class=\"c\" style=\"left:1px;top:14px;\"></div><div class=\"c\" style=\"left:1px;top:15px;\"></div><div class=\"c\" style=\"left:2px;top:0px;\"></div><div class=\"c\" style=\"left:2px;top:1px;\"></div><div class=\"c\" style=\"left:2px;top:5px;\"></div><div class=\"c\" style=\"left:2px;top:6px;\"></div><div class=\"c\" style=\"left:2px;top:7px;\"></div><div class=\"c\" style=\"left:2px;top:8px;\"></div><div class=\"c\" style=\"left:2px;top:9px;\"></div><div class=\"c\" style=\"left:2px;top:10px;\"></div><div class=\"c\" style=\"left:2px;top:14px;\"></div><div class=\"c\" style=\"left:2px;top:15px;\"></div><div class=\"c\" style=\"left:3px;top:0px;\"></div><div class=\"c\" style=\"left:3px;top:1px;\"></div><div class=\"c\" style=\"left:3px;top:2px;\"></div><div class=\"c\" style=\"left:3px;top:6px;\"></div><div class=\"c\" style=\"left:3px;top:7px;\"></div><div class=\"c\" style=\"left:3px;top:8px;\"></div><div class=\"c\" style=\"left:3px;top:9px;\"></div><div class=\"c\" style=\"left:3px;top:13px;\"></div><div class=\"c\" style=\"left:3px;top:14px;\"></div><div class=\"c\" style=\"left:3px;top:15px;\"></div><div class=\"c\" style=\"left:4px;top:1px;\"></div><div class=\"c\" style=\"left:4px;top:2px;\"></div><div class=\"c\" style=\"left:4px;top:3px;\"></div><div class=\"c\" style=\"left:4px;top:7px;\"></div><div class=\"c\" style=\"left:4px;top:8px;\"></div><div class=\"c\" style=\"left:4px;top:12px;\"></div><div class=\"c\" style=\"left:4px;top:13px;\"></div><div class=\"c\" style=\"left:4px;top:14px;\"></div><div class=\"c\" style=\"left:5px;top:2px;\"></div><div class=\"c\" style=\"left:5px;top:3px;\"></div><div class=\"c\" style=\"left:5px;top:4px;\"></div><div class=\"c\" style=\"left:5px;top:11px;\"></div><div class=\"c\" style=\"left:5px;top:12px;\"></div><div class=\"c\" style=\"left:5px;top:13px;\"></div><div class=\"c\" style=\"left:6px;top:3px;\"></div><div class=\"c\" style=\"left:6px;top:4px;\"></div><div class=\"c\" style=\"left:6px;top:5px;\"></div><div class=\"c\" style=\"left:6px;top:10px;\"></div><div class=\"c\" style=\"left:6px;top:11px;\"></div><div class=\"c\" style=\"left:6px;top:12px;\"></div><div class=\"c\" style=\"left:7px;top:4px;\"></div><div class=\"c\" style=\"left:7px;top:5px;\"></div><div class=\"c\" style=\"left:7px;top:6px;\"></div><div class=\"c\" style=\"left:7px;top:9px;\"></div><div class=\"c\" style=\"left:7px;top:10px;\"></div><div class=\"c\" style=\"left:7px;top:11px;\"></div><div class=\"c\" style=\"left:8px;top:5px;\"></div><div class=\"c\" style=\"left:8px;top:6px;\"></div><div class=\"c\" style=\"left:8px;top:7px;\"></div><div class=\"c\" style=\"left:8px;top:8px;\"></div><div class=\"c\" style=\"left:8px;top:9px;\"></div><div class=\"c\" style=\"left:8px;top:10px;\"></div><div class=\"c\" style=\"left:9px;top:6px;\"></div><div class=\"c\" style=\"left:9px;top:7px;\"></div><div class=\"c\" style=\"left:9px;top:8px;\"></div><div class=\"c\" style=\"left:9px;top:9px;\"></div><div class=\"c\" style=\"left:10px;top:7px;\"></div><div class=\"c\" style=\"left:10px;top:8px;\"></div> \n"
		"  \n"
		"               </div> </div> </a>\n"
		"  \n"
		"      </div> \n"
		"  \n"
		"  <script type='text/javascript' language='JavaScript'> \n"
		"  <!-- \n"
		"	"
		"  \n"
		"  var initads=%2%; \n"
		"  \n"
		"  \n"
		"  function init() { \n"
		"      if (arguments.callee.done) return; \n"
		"      arguments.callee.done = true; \n"
		"  	JsonToAds(initads); \n"
		"  	showAds(cursor,cursor + count); \n"
		"  	k=ads.length; \n"
		"  	cursor+=count; \n"
		"  	document.getElementById('nav_l').style.display='block'; \n"
		"  	arrowBgColor = document.getElementById('nav_l').style.backgroundColor; \n"
		"  	arrowColor = document.getElementById('nav_l').style.color; \n"
		"  	hoverColor = (arrowBgColor/2 + arrowColor/2); \n"
		"  } \n"
		"  \n"
		"  if (document.addEventListener) { \n"
		"      document.addEventListener(\"DOMContentLoaded\", init, false); \n"
		"  } \n"
		"  \n"
		"  if (/WebKit/i.test(navigator.userAgent)) { \n"
		"      var _timer = setInterval(function() { \n"
		"          if (/loaded|complete/.test(document.readyState)) { \n"
		"              clearInterval(_timer); \n"
		"              delete _timer; \n"
		"              init(); \n"
		"          } \n"
		"      }, 10); \n"
		"  } \n"
		"  window.onload = init; \n"
		"  \n"
		"  var count=%3%; \n"
		"  var cursor=0; \n"
		"  var k=0; \n"
		"  var t=Math.floor(10/count); \n"
		"  var _sem=false; \n"
		"  var _click = true; \n"
		"  var ads=new Array(); \n"
		"  var guids=\"\"; \n"
		"  var adsView=\"\"; \n"
		"  var imgs = new Image(); \n"
		"  var _m=false;\n"
		"  function showAds(start,end){ \n"
		"  	adsView=\"\"; \n"
		"  	document.getElementById('adsContainer').innerHTML =\"\"; \n"
		"  	if (end >= ads.length) { \n"
		"  		start = ads.length - (end - start); \n"
		"  		end = ads.length; \n"
		"  	} \n"
		"  \n"
		"  	for (i = start; i < end; i++) { \n"
		"  		if(ads[i]) \n"
		"  			adsView+=ads[i]; \n"
		"  	} \n"
		"  	document.getElementById('adsContainer').innerHTML = adsView; \n"
		"  } \n"
		"  function JsonToAds(r){ \n"
		"  	for(i=0;i<r.length;i++) \n"
		"  	{ \n"
		"  	if (r[i]['title'] != \"\") { \n"
		"  		ads[i + k] = '<div class=\"advBlock\" onmousemove=\"_mv(this);\"><a class=\"advHeader\" onmousedown=\"_md(this);\" href=\"' + r[i]['url'] + '&p=h&m=0&h=0\" target=\"_blank\" >' + r[i]['title'] + \n"
		"  		'</a><a class=\"advDescription\" onmousedown=\"_md(this);\" href=\"' + \n"
		"  		r[i]['url'] + \n"
		"  		'&p=d&m=0&h=0\" target=\"_blank\" >' + \n"
		"  		r[i]['description'] + \n"
		"  		'</a><a class=\"advCost\" onmousedown=\"_md(this);\" href=\"' + \n"
		"  		r[i]['url'] + \n"
		"  		'&p=p&m=0&h=0\" target=\"_blank\" >' + \n"
		"  		r[i]['price'] + \n"
		"  		'</a><a href=\"' + \n"
		"  		r[i]['url'] + \n"
		"  		'&p=i&m=0&h=0\" target=\"_blank\" onmousedown=\"_md(this);\" ><img class=\"advImage\" src=\"' + \n"
		"  		r[i]['image'] + \n"
		"  		'\" alt=\"' + \n"
		"  		r[i]['title'] + \n"
		"  		'\"></a></div>'; \n"
		"  		guids += r[i]['id'] + \"_\"; \n"
		"  		imgs.src = r[i]['image']; \n"
		"  	} \n"
		"  	else \n"
		"  	k-=1; \n"
		"  	} \n"
		"  	 k=ads.length; \n"
		"  \n"
		"  	if(k>=t*count)k=t*count; \n"
		"  } \n"
		"  function getXmlHttp(){ \n"
		"  	try { \n"
		"  		return new ActiveXObject(\"Msxml2.XMLHTTP\"); \n"
		"  	} catch (e) { \n"
		"          try { \n"
		"              return new ActiveXObject(\"Microsoft.XMLHTTP\"); \n"
		"          } catch (ee) { } \n"
		"      } \n"
		"      if (typeof XMLHttpRequest!='undefined') { \n"
		"          return new XMLHttpRequest(); \n"
		"  \n"
		"      } \n"
		"  } \n"
		"  \n"
		"  function pre_load(){ \n"
		"  	var params = 'exclude=' + encodeURIComponent(guids) + \"&rand=\" + Math.floor(Math.random() * 1000000); \n"
		"  	var xmlhttp = getXmlHttp(); \n"
		"  	xmlhttp.open(\"GET\", \"%4%\"+params, true) \n"
		"  \n"
		"  	xmlhttp.onreadystatechange=function(){ \n"
		"    if (xmlhttp.readyState != 4) return \n"
		"  \n"
		"    clearTimeout(timeout) \n"
		"  \n"
		"    if (xmlhttp.status == 200) { \n"
		"  	eval(\"var responsedata = (\" + xmlhttp.responseText + \")\"); \n"
		"  	if (responsedata.length > 0) { \n"
		"  		JsonToAds(responsedata); \n"
		"  		showAds(cursor, cursor + count); \n"
		"  		_sem = true; \n"
		"  		cursor += count; \n"
		"  		if (cursor > count) \n"
		"  			document.getElementById('nav_r').style.display = 'block'; \n"
		"  		if ((cursor) >= t * count) { \n"
		"  			document.getElementById('nav_l').style.display = 'none'; \n"
		"  		} \n"
		"  		else \n"
		"  			document.getElementById('nav_l').style.display = 'block'; \n"
		"  	} \n"
		"    } \n"
		"    else { \n"
		"  	handleError(\"Опаньки\"); \n"
		"    } \n"
		"  } \n"
		"  \n"
		"  xmlhttp.send(null); \n"
		"  \n"
		"  var timeout = setTimeout( function(){ xmlhttp.abort(); handleError(\"Time over\") },10000); \n"
		"  function handleError(message){if(ads.length>0) return; /*document.getElementById('nav_l').style.display='block';*/document.getElementById('adsContainer').innerHTML =\"<div>Опаньки!<br />Загрузка данных прервана:(</div>\";pre_load();} \n"
		"  \n"
		"  } \n"
		"  \n"
		"  function next(){ \n"
		"   document.getElementById('nav_l').style.display='none'; \n"
		"  	adsView=\"\"; \n"
		"  \n"
		"  	if (true || ads.length < t * count && cursor >= ads.length) { \n"
		"  		pre_load(); \n"
		"  	} \n"
		"  	else \n"
		"  	{ \n"
		"  		if (cursor >= count) \n"
		"  			document.getElementById('nav_l').style.display = 'none'; \n"
		"  		else \n"
		"  			document.getElementById('nav_l').style.display = 'block'; \n"
		"  \n"
		"  		if ((cursor) >= ads.length) { \n"
		"  			cursor = ads.length - count; \n"
		"  			document.getElementById('nav_l').style.display = 'none'; \n"
		"  		} \n"
		"  \n"
		"  		showAds(cursor,cursor + count); \n"
		"  		cursor += count; \n"
		"  		document.getElementById('nav_r').style.display = 'block'; \n"
		"  		_sem = false; \n"
		"  		_click = false; \n"
		"  	} \n"
		"  } \n"
		"  function prev(){ \n"
		"  	adsView=\"\"; \n"
		"  	cursor-=count; \n"
		"  	if(cursor-count<0)cursor=0+count; \n"
		"  	var start=cursor-count; \n"
		"  	if(start<0)start=0; \n"
		"  	showAds(start,start+count); \n"
		"  	if(count>=cursor)document.getElementById('nav_r').style.display='none'; \n"
		"  	if(cursor<ads.length)document.getElementById('nav_l').style.display='block'; \n"
		"  } \n"
		"  function change(cl){ \n"
		"  	var divs = document.getElementsByTagName(\"DIV\"); \n"
		"  	for (var i = 0; i < divs.length; i++) { \n"
		"  		if (divs[i].className == cl) \n"
		"  		divs[i].className=cl+'2'; \n"
		"  	} \n"
		"  } \n"
		"  \n"
		"  function change1(cl){ \n"
		"  	var divs = document.getElementsByTagName(\"DIV\"); \n"
		"  	for (var i = 0; i < divs.length; i++) { \n"
		"  		if (divs[i].className == cl+\"2\") \n"
		"  			divs[i].className=cl; \n"
		"  		if (divs[i].className == cl + \"2\") \n"
		"  			divs[i].className=cl+'1'; \n"
		"  	} \n"
		"  } \n"
		"function _mv(obj){\n"
		"	_m=true;\n"
		"}\n"
		"function _md(obj){\n"		
		"if(_m) obj.setAttribute('href',obj.getAttribute('href').replace('&m=0','&m=1'));"
		"obj.setAttribute('href',obj.getAttribute('href').replace('&h=0','&h=1'));\n"
		"}\n"
		"\n"
		" // -->"
		"  </script> \n"
		"</body>\n"
		"</html>\n";
	return true;
}



/** Шаблон информера с баннером со следующими подстановками:

    %1%	    CSS
    %2%	    swfobject (пришлось делать так, ибо в текстве библиотеки есть символ '%' и boost думает, что туда надо подставлять, что приводит к ошибке во время выполнения программы). swfobject можно получить у InformerTemplate с помощью метода getSwfobjectLibStr().
	%3%	    JSON для initads (баннер)
*/
bool InformerTemplate::initBannersTemplate(const string& filename)
{
	if (bannersTemplate!="")
	{
		return true;
	}

	string str;
	ifstream input (filename);
	if(input.fail())
	{
		return false;
	}
	while(getline(input,str))
	{
		swfobjectLibStr += (str + "\n");
	}
	input.close();

	//считали библиотеку успешно. инициализируем шаблон весь.

	bannersTemplate = 
		"<html>\n"
		"<head>\n"
		"<META http-equiv=\"Content-Type\" content=\"text/html; charset=utf-8\">\n"
		"<meta name=\"robots\" content=\"nofollow\" />\n"
		"<style type=\"text/css\">html, body {padding: 0; margin: 0; border: 0;}</style>\n\n"

		"\n"
		" %1% \n"
		"\n\n"

		"</head> \n"
		"<body> \n"
		"  <div id=\"mainContainer\"> \n\n"

		"   <div id='adsContainer'></div> \n"
		"   <div id=\"adInfo\"><a href=\"http://yottos.ru/Рекламные_программы\" target=\"_blank\" title=\"Реклама от Yottos\"></a></div>\n"
		"   </div> \n\n"


		"  <script type='text/javascript' language='JavaScript'>\n"
		" %2% \n" 
		"  </script>\n"

		"  <script type='text/javascript' language='JavaScript'> \n"
		"  <!-- \n\n"

		"  var initads=%3%; \n\n"


		"  function init() { \n"
		"     if (arguments.callee.done) return; \n"
		"      arguments.callee.done = true; \n"
		"  	JsonToAds4Banners(initads); \n"
		"  	showAds(cursor,cursor + count); \n"
		"  	k=ads.length; \n"
		"  	cursor+=count; \n"
		"  	document.getElementById('nav_l').style.display='block'; \n"
		"  	arrowBgColor = document.getElementById('nav_l').style.backgroundColor; \n"
		"  	arrowColor = document.getElementById('nav_l').style.color; \n"
		"  	hoverColor = (arrowBgColor/2 + arrowColor/2); \n"
		"  } \n\n"

		"  if (document.addEventListener) { \n"
		"      document.addEventListener(\"DOMContentLoaded\", init, false); \n"
		"  } \n\n"

		"  if (/WebKit/i.test(navigator.userAgent)) { \n"
		"      var _timer = setInterval(function() { \n"
		"          if (/loaded|complete/.test(document.readyState)) { \n"
		"              clearInterval(_timer); \n"
		"              delete _timer; \n"
		"              init(); \n"
		"          } \n"
		"      }, 10); \n"
		"  } \n"
		"  window.onload = init; \n\n"

		"  var count=1; \n"
		"  var cursor=0; \n"
		"  var k=0; \n"
		"  var t=Math.floor(10/count); \n"
		"  var ads=new Array(); \n"
		"  var adsView=\"\"; \n"
		"  var imgs = new Image(); \n"
		"  var _m=false;\n"
		"  function showAds(start,end){ \n"
		"  	adsView=\"\"; \n"
		"  	document.getElementById('adsContainer').innerHTML =\"\"; \n"
		"  	if (end >= ads.length) { \n"
		"  		start = ads.length - (end - start); \n"
		"  		end = ads.length; \n"
		"  	} \n\n"

		"  	for (i = start; i < end; i++) { \n"
		" 		if(ads[i])		\n"
		"  			adsView+=ads[i]; \n"
		"  	} \n"
		"  	document.getElementById('adsContainer').innerHTML = adsView;\n"
		"	if(initads[0]['description'].indexOf(\".swf\")==(initads[0]['description'].length-4)){\n"
		"		var xxx = initads[0]['url'] + \"&p=i&m=0&h=0\";\n"
		"		swfobject.embedSWF(initads[0]['description'], \"adsContainer\", initads[0]['width'], initads[0]['height'], \"9\", null, {redirectUrl:xxx}, {menu:\"false\", wmode:\"opaque\"});\n"
		"	}\n"
		"  } \n"
		"  function JsonToAds4Banners(r){\n"
		"	i=0;\n"
		"	if (r[i]['title'] != \"\") { \n"
		"  		ads[i + k] = '<div class=\"advBlock\" onmousemove=\"_mv(this);\"><a href=\"' + \n"
		"  		r[i]['url'] + \n"
		"  		'&p=i&m=0&h=0\" target=\"_blank\" onmousedown=\"_md(this);\" ><img class=\"advImage\" src=\"' + \n"
		"  		r[i]['image'] + \n"
		"  		'\" alt=\"' + \n"
		"  		r[i]['title'] + \n"
		"  		'\"></a></div>';\n"
		"  		imgs.src = r[i]['image']; \n"
		"  	} \n"
		"  	else \n"
		"  	k-=1; \n\n"

		"  	k=ads.length; \n\n"

		"  	if(k>=t*count)k=t*count; \n"
		"  } \n\n"

		"function _mv(obj){\n"
		"	_m=true;\n"
		"}\n"
		"function _md(obj){\n"
		"if(_m) obj.setAttribute('href',obj.getAttribute('href').replace('&m=0','&m=1'));obj.setAttribute('href',obj.getAttribute('href').replace('&h=0','&h=1'));\n"
		"}\n\n"

		" // -->  </script> \n"
		"</body>\n"
		"</html>\n";


	return true;
}


bool InformerTemplate::init()
{
	return (initTeasersTemplate() && initBannersTemplate("swfobject.js"));
}
