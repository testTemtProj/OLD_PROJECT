function buildSearchUrl(sender) {
    function getSearchUrl(href) {
        var r = /yottos\.(com\.ua|com|ru)/;
        var domain = window.location.host.match(r);
        var host = domain ? ('http://' + domain[0] + '/') : 'http://yottos.ru/';
        var lang = domain ? domain[1] : 'ru';
        var link = '';
        var txtControl = document.getElementById("searchString") ||
                         document.getElementById("QueryTextBox") ||
                         document.getElementById("ctl00_SearchString1_QueryTextBox") ||
                         document.getElementById("ctl00_QueryTextBox") || 
                         document.getElementById("SearchString_QueryTextBox") ||
						 document.getElementById("querytext") ||
						 document.getElementById("QueryText");
      
        var query = txtControl.value.replace(/[:;]/g, '');
        if (!txtControl || !txtControl.value) query='';
        switch (lang) {
            case 'com.ua':
                link = (href.match('news\.yottos\.') && ("http://news.yottos.com.ua/Поиск?" + query)) ||
                       (href.match('rynok\.yottos\.') && ("http://rynok.yottos.com.ua/поиск/" + query)) ||
                       (href.match('catalog\.yottos\.') && ("http://catalog.yottos.com.ua/yottos-каталог/Поиск/" + query)) ||
                       (href.match('zero\.yottos\.') && ("http://zero.yottos.com.ua/Zero.aspx?q=" + query)) ||
                       ("http://yottos.com.ua/Результат/" + query);
            case 'com':
                link = (href.match('news\.yottos\.') && ("http://news.yottos.com/Поиск?" + query)) ||
                       (href.match('rynok\.yottos\.') && ("http://rynok.yottos.com/поиск/" + query)) ||
                       (href.match('catalog\.yottos\.') && ("http://catalog.yottos.com/yottos-каталог/Поиск/" + query)) ||
                       (href.match('zero\.yottos\.') && ("http://zero.yottos.com/Zero.aspx?q=" + query)) ||
                       ("http://yottos.com/Результат/" + query);
            case 'ru':
            default:
                link = (href.match('news\.yottos\.') && ("http://news.yottos.ru/Поиск?" + query)) ||
                       (href.match('rynok\.yottos\.') && ("http://rynok.yottos.ru/поиск/" + query)) ||
                       (href.match('catalog\.yottos\.') && ("http://catalog.yottos.ru/yottos-каталог/Поиск/" + query)) ||
                       (href.match('zero\.yottos\.') && ("http://zero.yottos.ru/Zero.aspx?q=" + query)) ||
                       ("http://yottos.ru/Результат/" + query);
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