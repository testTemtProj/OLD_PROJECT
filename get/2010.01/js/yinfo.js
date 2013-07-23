(function () {
    var num = 0;
    function src() {
        return 'http://getmyad.yottos.com/sendstats.ashx?p=' + encodeURIComponent(window.location.href) +
               "&r=" + encodeURIComponent(document.referrer) +
               "&ses=" + encodeURIComponent(window.yottos_session) +
               "&ua=" + encodeURIComponent(navigator.userAgent)
               + "&w=" + screen.width
               + "&h=" + screen.height
               + "&n=" + num
		+ "&rand=" + Math.random() * 100000
               ;
    }

    function SendStats() {
        document.getElementById("ysjf").setAttribute("src", src());
        num++;
    };
    var intout = setTimeout(SendStats, 3000);
    var intervalSend = setInterval(SendStats, 15000);
    var pattern = /.*yottos\.com.*ses=([^&]*)/;
    var m = window.location.href.match(pattern);
    window.yottos_session = window.yottos_session || (m && m[1]) || Math.floor(Math.random() * 1000000);
    document.write("<iframe src='" + src() + "' style='display:none;' id='ysjf'></iframe>");
})();