function buildSearchUrl(sender) {
    function getSearchUrl(href) {
        var r = /yottos\.(com\.ua|ru|com)/;
        var domain = window.location.host.match(r);
        var host = domain ? ('http://' + domain[0] + '/') : 'http://yottos.ru/';
        var lang = domain ? domain[1] : 'ru';
        var link = '';
        var txtControl = document.getElementById("searchString") ||
                         document.getElementById("QueryTextBox") ||
                         document.getElementById("ctl00_SearchString1_QueryTextBox") ||
                         document.getElementById("ctl00_QueryTextBox") ||
                         document.getElementById("SearchString_QueryTextBox");
        if (!txtControl || !txtControl.value) return href;
        var query = txtControl.value.replace(/[:;]/g, '');

        switch (lang) {
            case 'com.ua':
                link = (href.match('news\.yottos\.') && ("http://news.yottos.com.ua/Поиск?" + query)) ||
                       (href.match('rynok\.yottos\.') && ("http://rynok.yottos.com.ua/поиск/" + query)) ||
                       (href.match('catalog\.yottos\.') && ("http://catalog.yottos.com.ua/yottos-каталог/Поиск/" + query)) ||
                       (href.match('zero\.yottos\.') && ("http://zero.yottos.com.ua/Zero.aspx?q=" + query)) ||
                       ("http://yottos.com.ua/Результат?" + query);
                break;
            case 'com':
                link = (href.match('news\.yottos\.') && ("http://news.yottos.com/Поиск?" + query)) ||
                       (href.match('rynok\.yottos\.') && ("http://rynok.yottos.com/поиск/" + query)) ||
                       (href.match('catalog\.yottos\.') && ("http://catalog.yottos.com/yottos-каталог/Поиск/" + query)) ||
                       (href.match('zero\.yottos\.') && ("http://zero.yottos.com/Zero.aspx?q=" + query)) ||
                       ("http://yottos.com/Результат?" + query);
                break;
            case 'ru':
            default:
                link = (href.match('news\.yottos\.') && ("http://news.yottos.ru/Поиск?" + query)) ||
                       (href.match('rynok\.yottos\.') && ("http://rynok.yottos.ru/поиск/" + query)) ||
                       (href.match('catalog\.yottos\.') && ("http://catalog.yottos.ru/yottos-каталог/Поиск/" + query)) ||
                       (href.match('zero\.yottos\.') && ("http://zero.yottos.ru/Zero.aspx?q=" + query)) ||
                       ("http://yottos.ru/Результат?" + query);
                break;
        }
        return query ? link : (link.match(/^http:\/\/[^\/]*\//)[0] || link);           // Если запрос пустой, возвращает ссылку на домен
    }

    sender.href = getSearchUrl(sender.href);
    return true;
}





/*




var webSearchPrefix = "/Результат/";
var zeroSearchPrefix = "Zero.aspx?q=";
var newsSearchPrefix = "/AllNews.aspx?q=";
var catalogSearchPrefix = "/CatalogSearch.aspx?q=";
var rynokSearchPrefix = "/AllResult.aspx?q=";

function buildSearchQuery_Transformed(hyperLink, searchPerfix) {
var newUrl = 'http://' + hyperLink.href.match(/:\/\/(.[^\/]+)/)[1];
var searchText = "";
var searchTextBox = document.form1.QueryTextBox;    
if (searchTextBox == null) searchTextBox = document.getElementById("ctl00_SearchString1_QueryTextBox");
if (searchTextBox == null) searchTextBox = document.aspnetForm.ctl00_QueryTextBox;
if (searchTextBox != null) searchText = escape(searchTextBox.value).replace(";", "");
if (searchText != "") newUrl += (searchPerfix + searchText);
else if (searchPerfix == zeroSearchPrefix) newUrl += "Zero/О_Zero";
hyperLink.href = newUrl;
return 1;
}

*/







function querybuild(hl) {
    if (window.RegExp) {
        var ue = hl.href;
        var qe = escape(document.aspnetForm.ctl00_QueryTextBox.value);
        if (ue.indexOf("q=") != -1) { hl.href = ue.replace(new RegExp("q=[^&$]*"), "q=" + qe); }
        else { hl.href = ue + "?q=" + qe; }
    }
    return 1;
}



/*var webSearchPrefix = "Result/";
var zeroSearchPrefix = "Zero/";*/

var webSearchPrefix = "Result.aspx?q=";
var zeroSearchPrefix = "Zero.aspx?q=";

var newsSearchPrefix = "/Search?";
var catalogSearchPrefix = "/yottos-catalog/Search/";
var rynokSearchPrefix = "/AllResult.aspx?q=";

var dimainExt = ".ru";
var docDomain = document.domain;
var indexOfDot = docDomain.lastIndexOf(".");
if (indexOfDot > 0) {
    dimainExt = docDomain.substring(indexOfDot);
}
switch (dimainExt) {
    case ".ru":
        newsSearchPrefix = "/Поиск?";
        break;
    case ".ua":
	dimainExt = ".com.ua"
        newsSearchPrefix = "/Пошук?";
        break;        
}

function buildSearchQuery_Transformed(hyperLink, searchPerfix) {
    var newUrl = "";    
    switch (searchPerfix) {
        case webSearchPrefix:
        case zeroSearchPrefix:
            newUrl = "http://www.yottos" + dimainExt + "/";
            break;
        case newsSearchPrefix:
            newUrl = "http://news.yottos" + dimainExt;
            break;
        case catalogSearchPrefix:
            newUrl = "";
            break;
        case rynokSearchPrefix:
            newUrl = "http://rynok.yottos" + dimainExt;
    }
    var searchText = "";
    var searchTextBox = document.aspnetForm.ctl00_QueryTextBox;
    if (searchTextBox == null) searchTextBox = document.getElementById("ctl00_SearchString1_QueryTextBox");
    if (searchTextBox == null) searchTextBox = document.aspnetForm.ctl00_QueryTextBox;
    if (searchTextBox != null) searchText = escape(searchTextBox.value).replace(";", "");
    if (searchText != "") newUrl += (searchPerfix + searchText);
    else if (searchPerfix == zeroSearchPrefix) newUrl += "Zero/zeroabout.aspx";  //newUrl += "Zero/AboutZero";
    hyperLink.href = newUrl;
    return 1;
}