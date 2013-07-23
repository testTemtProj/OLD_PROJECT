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