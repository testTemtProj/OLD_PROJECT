(function(){
    function src(){
        var id;
        try {
            id = yottos_id;
        }
        catch (e) {
            id = "Unknown";
        }

        window.yottos_session = window.yottos_session || Math.floor(Math.random() * 1000000);
        var url = 'http://attractor.yottos.com/tick';
        return url +
                '?p=' + encodeURIComponent(window.location.href) +
                "&r=" + encodeURIComponent(document.referrer) +
                "&ses=" + encodeURIComponent(window.yottos_session) +
                "&w=" + screen.width +
                "&h=" + screen.height +
                "&x=" + id;
    }

    var _src = src();
    document.write("<iframe src='" + "http://attractor.yottos.com/ysjif.html#"+ _src + "' style='display:none;' id='ysjif' name='ysjif'></iframe>");
})();
