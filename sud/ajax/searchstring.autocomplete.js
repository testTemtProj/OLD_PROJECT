var startTime = new Date;
var brName = navigator.appName;
var updateOpera = false;
var updateExplorer = false;
if (brName == "Opera" && parseFloat(navigator.appVersion) < 9.5) updateOpera = true;
else if (brName == "Microsoft Internet Explorer" && parseFloat((new RegExp("MSIE ([0-9]{1,}[.0-9]{0,})")).exec(navigator.userAgent)[1]) < 6) updateExplorer = true;
if (!updateOpera && !updateExplorer) {
    curTheme = "";
    $(function() {
        var endTime = new Date;
        var t = endTime - startTime;
        var d;
        d = 150;
        function format(item) {
            return item.term;
        }

        var txt = document.getElementById("SearchString_QueryTextBox") ||
                  document.getElementById("searchString") ||
                  document.getElementById("ctl00_SearchString1_QueryTextBox");          // TODO: не работает на странице About
        if (!txt)
		 return;
        txt = $(txt);
        if (!txt.autocomplete) {
		return;
	}
        txt.autocomplete("/suggest.fcgi", { multiple: false, max: 80, appendTo: "#divQueryBox", selectFirst: false, width: txt.width() + 4, maxColumnWidth: txt.width(), delay: d, spaceToContinue: true, parse: function(data) {
	    console.log(data);
            return $.map(eval(data), function(rowTheme) {
                var theme = rowTheme.t;
                var terms = $.map(rowTheme.w, function(rowTerm) {
                    return { data: { theme: theme, term: rowTerm[0], childCount: rowTerm[1], charsEntered: rowTerm[2], dt: rowTerm[3] == undefined ? "" : rowTerm[3] }, value: rowTerm[0], result: rowTerm[0] }
                });
                return terms
            })
        }, formatItem: function(item) {
            return format(item)
        }
        }).result(function(e, item) {
            var o = document.getElementById("SearchString_SearchButton") || document.getElementById("SearchButton") || document.getElementById("ctl00_SearchString1_SearchButton");
            if (!o) return;
            o.focus();
            o.click()
        })
    })
};
