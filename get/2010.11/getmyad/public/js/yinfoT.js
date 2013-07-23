(function () {
    var num = 0;
    function src() {
        var id;
        try {
            id = yottos_id;
        } catch (e) {
            id = "Unknown";
        }

        return 'http://rynok.yottos.ru/sendstatsX.ashx?p=' + encodeURIComponent(window.location.href) +
               "&r=" + encodeURIComponent(document.referrer) +
               "&ses=" + encodeURIComponent(window.yottos_session) +
               "&ua=" + encodeURIComponent(navigator.userAgent)
               + "&w=" + screen.width
               + "&h=" + screen.height
               + "&n=" + num
               + "&x=" + id
		+ "&rand=" + Math.random() * 100000
               ;
    }

    function SendStats() {
        document.getElementById("ysjf").setAttribute("src", src());
        //pre_load();

        num++;
    };
    var intout = setTimeout(SendStats, 3000);
    var intervalSend = setInterval(SendStats, 15000);
    var pattern = /.*yottos\.com.*ses=([^&]*)/;
    var m = window.location.href.match(pattern);
    window.yottos_session = window.yottos_session || (m && m[1]) || Math.floor(Math.random() * 1000000);
    document.write("<img src='" + src() + "' style='display:none;' id='ysjf'></img>");
    function getXmlHttp() {
        try {
            return new ActiveXObject("Msxml2.XMLHTTP");
        }
        catch (e) {
            try {
                return new ActiveXObject("Microsoft.XMLHTTP");
            }
            catch (ee) {
            }
        }
        if (typeof XMLHttpRequest != 'undefined') {
            return new XMLHttpRequest();
        }
    }
    function pre_load() {
        var xmlhttp = getXmlHttp();
        xmlhttp.open("GET", src(), true);
        xmlhttp.onreadystatechange = function () {

            if (xmlhttp.readyState != 4) return;
            clearTimeout(timeout);
            if (xmlhttp.status == 200);
        }
        var timeout = setTimeout(function () { xmlhttp.abort(); }, 10000);
    }

})();


