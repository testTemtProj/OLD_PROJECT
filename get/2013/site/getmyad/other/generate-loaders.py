#!/usr/bin/python
# encoding: utf-8
from time import sleep
from ftplib import FTP
import pymongo
import StringIO, codecs
import re
from sys import argv
import json
import urllib2
from urlparse import urlparse

from slimit import minifier

def _generate_informer_loader(informer_id):
    ''' Возвращает код javascript-загрузчика информера '''
    db = pymongo.Connection(host='yottos.ru,213.186.121.76:27018,213.186.121.199:27018').getmyad_db
    adv = db.informer.find_one({'guid': informer_id.lower()})
    if not adv:
        return False
    try:
        guid = adv['guid']
        width = int(re.match('[0-9]+',
                    adv['admaker']['Main']['width']).group(0))
        height = int(re.match('[0-9]+',
                    adv['admaker']['Main']['height']).group(0))
    except:
        raise Exception("Incorrect size dimensions for informer %s" % informer_id)
    try:
        border = int(re.match('[0-9]+',
                    adv['admaker']['Main']['borderWidth']).group(0))
    except:
        border = 1
    partner = adv.get('domain', 'other').replace('.', '-').replace('/', '')
    auto_reload = adv.get('auto_reload', 300)

    """
    domain = adv.get('domain', 'invalid.attractor.yottos.com')
    parsed_domain = urlparse(domain)
    site_url = 'http://' + (parsed_domain.hostname if parsed_domain.hostname else domain)
    secret_token = 'a4b03d409369e92ce4d8f088cd749b10' # admin account
    attractor_url = 'http://attractor.yottos.com/index.php?module=API&method=SitesManager.getSitesIdFromSiteUrl&url=' + site_url + '&format=json&token_auth=' + secret_token
    print attractor_url
    request = urllib2.Request(url=attractor_url)

    success = False
    while not success:
        try:
            response = urllib2.urlopen(request) 
            print 'successed'
            success = True
        except:
            pass

    try:
        site_id = json.loads(response.read())[0]['idsite']
    except:
        site_id = None

    """

    site_id = None

    width += border * 2
    height += border * 2
    script = (ur"""
        ;yottos_snowball_cache = typeof yottos_snowball_cache !== 'undefined' ? yottos_snowball_cache : {};
        ;function validate(string)
        {
            var utftext = "";
            for (var n = 0; n < string.length; n++) {
                var c = string.charCodeAt(n);
                    if((c > 47) && (c < 58))
                    {
                        utftext += String.fromCharCode(c);
                    }
                    else if ((c > 64) && (c < 91))
                    {
                        utftext += String.fromCharCode(c);
                    }
                    else if ((c > 96) && (c < 123))
                    {
                        utftext += String.fromCharCode(c);
                    }
                    else if ((c > 1039) && (c < 1104))
                    {
                        utftext += String.fromCharCode(c);
                    }
                    else
                    {
                        utftext += String.fromCharCode(32);
                    }
            }
            return utftext;
        }
        ;function getContext(){
            ;function yottos_Snowball(lng) {
                    function Among(s, substring_i, result, method) {
                        this.s_size = s.length;
                        this.s = this.toCharArray(s);
                        this.substring_i = substring_i;
                        this.result = result;
                        this.method = method;
                    }
                    Among.prototype.toCharArray = function(s) {
                        var sLength = s.length, charArr = new Array(sLength);
                        for (var i = 0; i < sLength; i++)
                            charArr[i] = s.charCodeAt(i);
                        return charArr;
                    }
                    function SnowballProgram() {
                        var current;
                        return {
                            b : 0,
                            k : 0,
                            l : 0,
                            c : 0,
                            lb : 0,
                            s_c : function(word) {
                                current = word;
                                this.c = 0;
                                this.l = word.length;
                                this.lb = 0;
                                this.b = this.c;
                                this.k = this.l;
                            },
                            g_c : function() {
                                var result = current;
                                current = null;
                                return result;
                            },
                            i_g : function(s, min, max) {
                                if (this.c < this.l) {
                                    var ch = current.charCodeAt(this.c);
                                    if (ch <= max && ch >= min) {
                                        ch -= min;
                                        if (s[ch >> 3] & (0X1 << (ch & 0X7))) {
                                            this.c++;
                                            return true;
                                        }
                                    }
                                }
                                return false;
                            },
                            i_g_b : function(s, min, max) {
                                if (this.c > this.lb) {
                                    var ch = current.charCodeAt(this.c - 1);
                                    if (ch <= max && ch >= min) {
                                        ch -= min;
                                        if (s[ch >> 3] & (0X1 << (ch & 0X7))) {
                                            this.c--;
                                            return true;
                                        }
                                    }
                                }
                                return false;
                            },
                            o_g : function(s, min, max) {
                                if (this.c < this.l) {
                                    var ch = current.charCodeAt(this.c);
                                    if (ch > max || ch < min) {
                                        this.c++;
                                        return true;
                                    }
                                    ch -= min;
                                    if (!(s[ch >> 3] & (0X1 << (ch & 0X7)))) {
                                        this.c++;
                                        return true;
                                    }
                                }
                                return false;
                            },
                            o_g_b : function(s, min, max) {
                                if (this.c > this.lb) {
                                    var ch = current.charCodeAt(this.c - 1);
                                    if (ch > max || ch < min) {
                                        this.c--;
                                        return true;
                                    }
                                    ch -= min;
                                    if (!(s[ch >> 3] & (0X1 << (ch & 0X7)))) {
                                        this.c--;
                                        return true;
                                    }
                                }
                                return false;
                            },
                            e_s : function(s_size, s) {
                                if (this.l - this.c < s_size)
                                    return false;
                                for (var i = 0; i < s_size; i++)
                                    if (current.charCodeAt(this.c + i) != s.charCodeAt(i))
                                        return false;
                                this.c += s_size;
                                return true;
                            },
                            e_s_b : function(s_size, s) {
                                if (this.c - this.lb < s_size)
                                    return false;
                                for (var i = 0; i < s_size; i++)
                                    if (current.charCodeAt(this.c - s_size + i) != s
                                            .charCodeAt(i))
                                        return false;
                                this.c -= s_size;
                                return true;
                            },
                            f_a : function(v, v_size) {
                                var i = 0, j = v_size, c = this.c, l = this.l, common_i = 0, common_j = 0, first_key_inspected = false;
                                while (true) {
                                    var k = i + ((j - i) >> 1), diff = 0, common = common_i < common_j
                                            ? common_i
                                            : common_j, w = v[k];
                                    for (var i2 = common; i2 < w.s_size; i2++) {
                                        if (c + common == l) {
                                            diff = -1;
                                            break;
                                        }
                                        diff = current.charCodeAt(c + common) - w.s[i2];
                                        if (diff)
                                            break;
                                        common++;
                                    }
                                    if (diff < 0) {
                                        j = k;
                                        common_j = common;
                                    } else {
                                        i = k;
                                        common_i = common;
                                    }
                                    if (j - i <= 1) {
                                        if (i > 0 || j == i || first_key_inspected)
                                            break;
                                        first_key_inspected = true;
                                    }
                                }
                                while (true) {
                                    var w = v[i];
                                    if (common_i >= w.s_size) {
                                        this.c = c + w.s_size;
                                        if (!w.method)
                                            return w.result;
                                        var res = w.method();
                                        this.c = c + w.s_size;
                                        if (res)
                                            return w.result;
                                    }
                                    i = w.substring_i;
                                    if (i < 0)
                                        return 0;
                                }
                            },
                            f_a_b : function(v, v_size) {
                                var i = 0, j = v_size, c = this.c, lb = this.lb, common_i = 0, common_j = 0, first_key_inspected = false;
                                while (true) {
                                    var k = i + ((j - i) >> 1), diff = 0, common = common_i < common_j
                                            ? common_i
                                            : common_j, w = v[k];
                                    for (var i2 = w.s_size - 1 - common; i2 >= 0; i2--) {
                                        if (c - common == lb) {
                                            diff = -1;
                                            break;
                                        }
                                        diff = current.charCodeAt(c - 1 - common) - w.s[i2];
                                        if (diff)
                                            break;
                                        common++;
                                    }
                                    if (diff < 0) {
                                        j = k;
                                        common_j = common;
                                    } else {
                                        i = k;
                                        common_i = common;
                                    }
                                    if (j - i <= 1) {
                                        if (i > 0 || j == i || first_key_inspected)
                                            break;
                                        first_key_inspected = true;
                                    }
                                }
                                while (true) {
                                    var w = v[i];
                                    if (common_i >= w.s_size) {
                                        this.c = c - w.s_size;
                                        if (!w.method)
                                            return w.result;
                                        var res = w.method();
                                        this.c = c - w.s_size;
                                        if (res)
                                            return w.result;
                                    }
                                    i = w.substring_i;
                                    if (i < 0)
                                        return 0;
                                }
                            },
                            r_s : function(c_bra, c_ket, s) {
                                var adjustment = s.length - (c_ket - c_bra), left = current
                                        .substring(0, c_bra), right = current.substring(c_ket);
                                current = left + s + right;
                                this.l += adjustment;
                                if (this.c >= c_ket)
                                    this.c += adjustment;
                                else if (this.c > c_bra)
                                    this.c = c_bra;
                                return adjustment;
                            },
                            s_ch : function() {
                                if (this.b < 0 || this.b > this.k || this.k > this.l
                                        || this.l > current.length)
                                    throw ("faulty slice operation");
                            },
                            s_f : function(s) {
                                this.s_ch();
                                this.r_s(this.b, this.k, s);
                            },
                            s_d : function() {
                                this.s_f("");
                            },
                            i_ : function(c_bra, c_ket, s) {
                                var adjustment = this.r_s(c_bra, c_ket, s);
                                if (c_bra <= this.b)
                                    this.b += adjustment;
                                if (c_bra <= this.k)
                                    this.k += adjustment;
                            },
                            s_t : function() {
                                this.s_ch();
                                return current.substring(this.b, this.k);
                            },
                            e_v_b : function(s) {
                                return this.e_s_b(s.length, s);
                            }
                        };
                    }
                    var stemFactory = {
                        RussianStemmer : function() {
                            var a_0 = [new Among("\u0432", -1, 1),
                                    new Among("\u0438\u0432", 0, 2),
                                    new Among("\u044B\u0432", 0, 2),
                                    new Among("\u0432\u0448\u0438", -1, 1),
                                    new Among("\u0438\u0432\u0448\u0438", 3, 2),
                                    new Among("\u044B\u0432\u0448\u0438", 3, 2),
                                    new Among("\u0432\u0448\u0438\u0441\u044C", -1, 1),
                                    new Among("\u0438\u0432\u0448\u0438\u0441\u044C", 6, 2),
                                    new Among("\u044B\u0432\u0448\u0438\u0441\u044C", 6, 2)], a_1 = [
                                    new Among("\u0435\u0435", -1, 1),
                                    new Among("\u0438\u0435", -1, 1),
                                    new Among("\u043E\u0435", -1, 1),
                                    new Among("\u044B\u0435", -1, 1),
                                    new Among("\u0438\u043C\u0438", -1, 1),
                                    new Among("\u044B\u043C\u0438", -1, 1),
                                    new Among("\u0435\u0439", -1, 1),
                                    new Among("\u0438\u0439", -1, 1),
                                    new Among("\u043E\u0439", -1, 1),
                                    new Among("\u044B\u0439", -1, 1),
                                    new Among("\u0435\u043C", -1, 1),
                                    new Among("\u0438\u043C", -1, 1),
                                    new Among("\u043E\u043C", -1, 1),
                                    new Among("\u044B\u043C", -1, 1),
                                    new Among("\u0435\u0433\u043E", -1, 1),
                                    new Among("\u043E\u0433\u043E", -1, 1),
                                    new Among("\u0435\u043C\u0443", -1, 1),
                                    new Among("\u043E\u043C\u0443", -1, 1),
                                    new Among("\u0438\u0445", -1, 1),
                                    new Among("\u044B\u0445", -1, 1),
                                    new Among("\u0435\u044E", -1, 1),
                                    new Among("\u043E\u044E", -1, 1),
                                    new Among("\u0443\u044E", -1, 1),
                                    new Among("\u044E\u044E", -1, 1),
                                    new Among("\u0430\u044F", -1, 1),
                                    new Among("\u044F\u044F", -1, 1)], a_2 = [
                                    new Among("\u0435\u043C", -1, 1),
                                    new Among("\u043D\u043D", -1, 1),
                                    new Among("\u0432\u0448", -1, 1),
                                    new Among("\u0438\u0432\u0448", 2, 2),
                                    new Among("\u044B\u0432\u0448", 2, 2),
                                    new Among("\u0449", -1, 1),
                                    new Among("\u044E\u0449", 5, 1),
                                    new Among("\u0443\u044E\u0449", 6, 2)], a_3 = [
                                    new Among("\u0441\u044C", -1, 1),
                                    new Among("\u0441\u044F", -1, 1)], a_4 = [
                                    new Among("\u043B\u0430", -1, 1),
                                    new Among("\u0438\u043B\u0430", 0, 2),
                                    new Among("\u044B\u043B\u0430", 0, 2),
                                    new Among("\u043D\u0430", -1, 1),
                                    new Among("\u0435\u043D\u0430", 3, 2),
                                    new Among("\u0435\u0442\u0435", -1, 1),
                                    new Among("\u0438\u0442\u0435", -1, 2),
                                    new Among("\u0439\u0442\u0435", -1, 1),
                                    new Among("\u0435\u0439\u0442\u0435", 7, 2),
                                    new Among("\u0443\u0439\u0442\u0435", 7, 2),
                                    new Among("\u043B\u0438", -1, 1),
                                    new Among("\u0438\u043B\u0438", 10, 2),
                                    new Among("\u044B\u043B\u0438", 10, 2),
                                    new Among("\u0439", -1, 1),
                                    new Among("\u0435\u0439", 13, 2),
                                    new Among("\u0443\u0439", 13, 2),
                                    new Among("\u043B", -1, 1),
                                    new Among("\u0438\u043B", 16, 2),
                                    new Among("\u044B\u043B", 16, 2),
                                    new Among("\u0435\u043C", -1, 1),
                                    new Among("\u0438\u043C", -1, 2),
                                    new Among("\u044B\u043C", -1, 2),
                                    new Among("\u043D", -1, 1),
                                    new Among("\u0435\u043D", 22, 2),
                                    new Among("\u043B\u043E", -1, 1),
                                    new Among("\u0438\u043B\u043E", 24, 2),
                                    new Among("\u044B\u043B\u043E", 24, 2),
                                    new Among("\u043D\u043E", -1, 1),
                                    new Among("\u0435\u043D\u043E", 27, 2),
                                    new Among("\u043D\u043D\u043E", 27, 1),
                                    new Among("\u0435\u0442", -1, 1),
                                    new Among("\u0443\u0435\u0442", 30, 2),
                                    new Among("\u0438\u0442", -1, 2),
                                    new Among("\u044B\u0442", -1, 2),
                                    new Among("\u044E\u0442", -1, 1),
                                    new Among("\u0443\u044E\u0442", 34, 2),
                                    new Among("\u044F\u0442", -1, 2),
                                    new Among("\u043D\u044B", -1, 1),
                                    new Among("\u0435\u043D\u044B", 37, 2),
                                    new Among("\u0442\u044C", -1, 1),
                                    new Among("\u0438\u0442\u044C", 39, 2),
                                    new Among("\u044B\u0442\u044C", 39, 2),
                                    new Among("\u0435\u0448\u044C", -1, 1),
                                    new Among("\u0438\u0448\u044C", -1, 2),
                                    new Among("\u044E", -1, 2),
                                    new Among("\u0443\u044E", 44, 2)], a_5 = [
                                    new Among("\u0430", -1, 1),
                                    new Among("\u0435\u0432", -1, 1),
                                    new Among("\u043E\u0432", -1, 1),
                                    new Among("\u0435", -1, 1),
                                    new Among("\u0438\u0435", 3, 1),
                                    new Among("\u044C\u0435", 3, 1),
                                    new Among("\u0438", -1, 1),
                                    new Among("\u0435\u0438", 6, 1),
                                    new Among("\u0438\u0438", 6, 1),
                                    new Among("\u0430\u043C\u0438", 6, 1),
                                    new Among("\u044F\u043C\u0438", 6, 1),
                                    new Among("\u0438\u044F\u043C\u0438", 10, 1),
                                    new Among("\u0439", -1, 1),
                                    new Among("\u0435\u0439", 12, 1),
                                    new Among("\u0438\u0435\u0439", 13, 1),
                                    new Among("\u0438\u0439", 12, 1),
                                    new Among("\u043E\u0439", 12, 1),
                                    new Among("\u0430\u043C", -1, 1),
                                    new Among("\u0435\u043C", -1, 1),
                                    new Among("\u0438\u0435\u043C", 18, 1),
                                    new Among("\u043E\u043C", -1, 1),
                                    new Among("\u044F\u043C", -1, 1),
                                    new Among("\u0438\u044F\u043C", 21, 1),
                                    new Among("\u043E", -1, 1), new Among("\u0443", -1, 1),
                                    new Among("\u0430\u0445", -1, 1),
                                    new Among("\u044F\u0445", -1, 1),
                                    new Among("\u0438\u044F\u0445", 26, 1),
                                    new Among("\u044B", -1, 1), new Among("\u044C", -1, 1),
                                    new Among("\u044E", -1, 1),
                                    new Among("\u0438\u044E", 30, 1),
                                    new Among("\u044C\u044E", 30, 1),
                                    new Among("\u044F", -1, 1),
                                    new Among("\u0438\u044F", 33, 1),
                                    new Among("\u044C\u044F", 33, 1)], a_6 = [
                                    new Among("\u043E\u0441\u0442", -1, 1),
                                    new Among("\u043E\u0441\u0442\u044C", -1, 1)], a_7 = [
                                    new Among("\u0435\u0439\u0448\u0435", -1, 1),
                                    new Among("\u043D", -1, 2),
                                    new Among("\u0435\u0439\u0448", -1, 1),
                                    new Among("\u044C", -1, 3)], g_v = [33, 65, 8, 232], I_p2, I_pV, sbp = new SnowballProgram();
                            this.setCurrent = function(word) {
                                sbp.s_c(word);
                            };
                            this.getCurrent = function() {
                                return sbp.g_c();
                            };
                            function habr3() {
                                while (!sbp.i_g(g_v, 1072, 1103)) {
                                    if (sbp.c >= sbp.l)
                                        return false;
                                    sbp.c++;
                                }
                                return true;
                            }
                            function habr4() {
                                while (!sbp.o_g(g_v, 1072, 1103)) {
                                    if (sbp.c >= sbp.l)
                                        return false;
                                    sbp.c++;
                                }
                                return true;
                            }
                            function r_mark_regions() {
                                I_pV = sbp.l;
                                I_p2 = I_pV;
                                if (habr3()) {
                                    I_pV = sbp.c;
                                    if (habr4())
                                        if (habr3())
                                            if (habr4())
                                                I_p2 = sbp.c;
                                }
                            }
                            function r_R2() {
                                return I_p2 <= sbp.c;
                            }
                            function habr2(a, n) {
                                var a_v, v_1;
                                sbp.k = sbp.c;
                                a_v = sbp.f_a_b(a, n);
                                if (a_v) {
                                    sbp.b = sbp.c;
                                    switch (a_v) {
                                        case 1 :
                                            v_1 = sbp.l - sbp.c;
                                            if (!sbp.e_s_b(1, "\u0430")) {
                                                sbp.c = sbp.l - v_1;
                                                if (!sbp.e_s_b(1, "\u044F"))
                                                    return false;
                                            }
                                        case 2 :
                                            sbp.s_d();
                                            break;
                                    }
                                    return true;
                                }
                                return false;
                            }
                            function r_perfective_gerund() {
                                return habr2(a_0, 9);
                            }
                            function habr1(a, n) {
                                var a_v;
                                sbp.k = sbp.c;
                                a_v = sbp.f_a_b(a, n);
                                if (a_v) {
                                    sbp.b = sbp.c;
                                    if (a_v == 1)
                                        sbp.s_d();
                                    return true;
                                }
                                return false;
                            }
                            function r_adjective() {
                                return habr1(a_1, 26);
                            }
                            function r_adjectival() {
                                var a_v;
                                if (r_adjective()) {
                                    habr2(a_2, 8);
                                    return true;
                                }
                                return false;
                            }
                            function r_reflexive() {
                                return habr1(a_3, 2);
                            }
                            function r_verb() {
                                return habr2(a_4, 46);
                            }
                            function r_noun() {
                                habr1(a_5, 36);
                            }
                            function r_derivational() {
                                var a_v;
                                sbp.k = sbp.c;
                                a_v = sbp.f_a_b(a_6, 2);
                                if (a_v) {
                                    sbp.b = sbp.c;
                                    if (r_R2() && a_v == 1)
                                        sbp.s_d();
                                }
                            }
                            function r_tidy_up() {
                                var a_v;
                                sbp.k = sbp.c;
                                a_v = sbp.f_a_b(a_7, 4);
                                if (a_v) {
                                    sbp.b = sbp.c;
                                    switch (a_v) {
                                        case 1 :
                                            sbp.s_d();
                                            sbp.k = sbp.c;
                                            if (!sbp.e_s_b(1, "\u043D"))
                                                break;
                                            sbp.b = sbp.c;
                                        case 2 :
                                            if (!sbp.e_s_b(1, "\u043D"))
                                                break;
                                        case 3 :
                                            sbp.s_d();
                                            break;
                                    }
                                }
                            }
                            this.stem = function() {
                                r_mark_regions();
                                sbp.c = sbp.l;
                                if (sbp.c < I_pV)
                                    return false;
                                sbp.lb = I_pV;
                                if (!r_perfective_gerund()) {
                                    sbp.c = sbp.l;
                                    if (!r_reflexive())
                                        sbp.c = sbp.l;
                                    if (!r_adjectival()) {
                                        sbp.c = sbp.l;
                                        if (!r_verb()) {
                                            sbp.c = sbp.l;
                                            r_noun();
                                        }
                                    }
                                }
                                sbp.c = sbp.l;
                                sbp.k = sbp.c;
                                if (sbp.e_s_b(1, "\u0438")) {
                                    sbp.b = sbp.c;
                                    sbp.s_d();
                                } else
                                    sbp.c = sbp.l;
                                r_derivational();
                                sbp.c = sbp.l;
                                r_tidy_up();
                                return true;
                            }
                        }}
                    var stemName = lng.substring(0, 1).toUpperCase()
                            + lng.substring(1).toLowerCase() + "Stemmer";
                    return new stemFactory[stemName]();
            }   
            ;var yottos_Stem = function(lng) {
                var yottos_testStemmer = new yottos_Snowball(lng);
                return function(word) {
                  yottos_testStemmer.setCurrent(word);
                  yottos_testStemmer.stem();
                  return yottos_testStemmer.getCurrent();
                }
            };
            ;function yottos_stremer(word){
                if (yottos_snowball_cache[word]){
                    w = yottos_snowball_cache[word];
                }
                else{
                    w = new yottos_Stem('russian')(word);
                    yottos_snowball_cache[word] = w;
                }
                return w;
            }; 
            function getText(){
                var result = '';
                result += (document.title.replace(/[^a-zA-Zа-яА-Я]/g,' ').replace(/\s+$/g,'').replace(/^\s+/g,'').replace(/[\n\t\r\f\s]{2,}/g,' '));
                var metas = document.getElementsByTagName('meta');
                if (metas) {
                    for (var x=0,y=metas.length; x<y; x++) {
                        if (metas[x].name.toLowerCase() == "description") {
                            result += ' ';
                            result += (metas[x].content.replace(/[^a-zA-Zа-яА-Я]/g,' ').replace(/\s+$/g,'').replace(/^\s+/g,'').replace(/[\n\t\r\f\s]{2,}/g,' ')) + ' ';
                        }
                        if (metas[x].name.toLowerCase() == "keywords") {
                            result += ' ';
                            result += (metas[x].content.replace(/[^a-zA-Zа-яА-Я]/g,' ').replace(/\s+$/g,'').replace(/^\s+/g,'').replace(/[\n\t\r\f\s]{2,}/g,' ')) + ' ';
                        }
                    }
                }
               return result;
            }
            var yottos_splitted = getText().toLowerCase().split(' ');
            var yottos_collector = {};
            var yottos_counter = {};
            var yottos_ignore = ['бол','больш','будет','будут','как','пок','коментар','будт','был','быт','вдруг','вед','впроч','всегд','всег','всех',
            'говор','главн','даж','друг','дальш','добав','есл','ест','жизн','зач','зде','иногд','кажет','кажд','как','когд','конечн','котор','куд',
            'лучш','либ','межд','мен','долж','смысл','след','чита','люб','постара','помим','числ','соб','ждат','част','использ','велик','член','некотор',
            'мног','может','можн','наконец','нег','нельз','нибуд','никогд','нич','один','опя','опубликова','перед','посл','пот','почт','разв','сво',
            'себ','сегодн','сейчас','сказа','совс','так','теб','тепер','тогд','тог','тож','тольк','хорош','хот','чег','человек','пут','вполн','возможн',
            'через','чтоб','чут','эт','позж','все','поэт','точн','этот','над','итог','недел','сведен','тем','город','гроз','зон','принят','балл','перв',
            'вход','лент','оста','мир','образ','идет','выйт','нол','сил','наш','мнен','одн','ищ','выш','взял','откр','нов','удив','всем','важн','ожида',
            'сам','ход','пущ','тег','выж','комментар','ваш','цен','коснут','слаб','ситуац','назов','уход','дол','основн','ряд','заверш','дополнен','влия',
            'описа','меньш','двум','слаб','стал','новост','отраз','вопрос','выбор','сдела','смерт','последн','поворот','высок','опозор','текст',
            'назов','основн','причин','групп','похож','with','that','this','about','above','after','again','against','because','been','before','being',
            'below','between','both','cannot','could','does','down','than','that','important','partner','border','link','text','radius','none','document',
            'height','color','title','normal','font','down','display','width','block','margin','yandex','item','type','left','padding','auto','inner',
            'function','decorati','google','position','http','align','webkit','inherit','direct','hover','referrer','write','size','math','spacing',
            'line','sizing','float','bottom','vert','charset','vertical','background','underline','visited','inline','unescape','value','style','visible',
            'address','else','true','tail','iframe','adriver','white','space','collapse','content','list','window','absolute','script','random','transparent',
            'repeat','scroll','container','piclayout','email','site','form','location','place','table','show','indent','visibility','clickable','last',
            'agewarn','opts','toggler','errormsg','getcode','href','relative','overflow','clear','cursor','outline','index','full','baseline','hide',
            'focus','catch','async','https','escape','round','target','blank','frameborder','scrolling','click','hidden','empty','cells','letter','static',
            'layout','transform','word','right','weight','warn','active','used','context','undefined','counter','page','mail','body','domain','region',
            'pointer','nowrap','family','first','data','online','push','metrika','callbacks','image','classname','protocol','init','icon','wrap','root',
            'solid','facebook','options','defaults','offset','false','return','like','opera','frames','typeof','decoration'];
                yottos_ignore = (function(){
                    var yottos_o = {};
                    var yottos_iCount = yottos_ignore.length;
                    for (var i=0;i<yottos_iCount;i++){
                        yottos_o[yottos_ignore[i]] = true;
                    }
                    return yottos_o;
                }());
                for (i = 0; i < yottos_splitted.length; i++) {
                   var yottos_key = yottos_splitted[i].replace(/^\s*/, "").replace(/\s*$/, "");
                   if (yottos_key.length > 3){
                        var yottos_streem_key = yottos_stremer(yottos_key);
                        if (!yottos_ignore[yottos_streem_key]) {
                            yottos_collector[yottos_streem_key] = yottos_key;
                            yottos_counter[yottos_streem_key] = yottos_counter[yottos_streem_key] || 0;
                            yottos_counter[yottos_streem_key]++;
                        }
                    }
                }
                var yottos_arr = [];
                for (yottos_sWord in yottos_counter) {
                    if (yottos_counter[yottos_sWord] > 1){
                        yottos_arr.push({
                        text: yottos_collector[yottos_sWord],
                        streem:yottos_sWord,
                        frequency: yottos_counter[yottos_sWord]
                        });
                    }
                }
                var yottos_sort_arr = yottos_arr.sort(function(a,b){return (a.frequency > b.frequency) ? -1 : ((a.frequency < b.frequency) ? 1 : 0);});
                var yottos_out = [];
                for (var i=0; i<yottos_sort_arr.length; i++) {
                    yottos_out.push(yottos_sort_arr[i].text);
                }

                ;var yottos_out_length = 0;
                ;var yottos_output = [];
                for (var i=0; i<yottos_out.length; i++)
                {
                    yottos_out_length += yottos_out[i].length;
                    if (navigator.appName == 'Microsoft Internet Explorer'){
                        if (yottos_out_length < 200) {
                            yottos_output.push(yottos_out[i]);
                        }
                    }
                    else{
                        if (yottos_out_length < 1000) {
                            yottos_output.push(yottos_out[i]);
                        }
                    }
                }
            return (yottos_output.join(' '));
        }
        ;function yottos_getSearch(){
            ;var result = "";
            ;var search_engines=[ 
                {"name":"Mail", "pattern":"go.mail.ru", "param":"q"}, 
                {"name":"Google", "pattern":"google.", "param":"q"}, 
                {"name":"Google", "pattern":"google.", "param":"as_q"}, 
                {"name":"Live Search", "pattern":"search.live.com", "param":"q"}, 
                {"name":"Bing", "pattern":"bing", "param":"q"}, 
                {"name":"Rambler", "pattern":"rambler.ru", "param":"query"}, 
                {"name":"Rambler", "pattern":"rambler.ru", "param":"words"}, 
                {"name":"Yahoo!", "pattern":"search.yahoo.com", "param":"p"}, 
                {"name":"Nigma", "pattern":"nigma.ru", "param":"s"}, 
                {"name":"Nigma", "pattern":"nigma.ru", "param":"q"}, 
                {"name":"MSN", "pattern":"search.msn.com", "param":"q"}, 
                {"name":"Ask", "pattern":"ask.com", "param":"q"}, 
                {"name":"QIP", "pattern":"search.qip.ru", "param":"query"}, 
                {"name":"RapidAll", "pattern":"rapidall.com", "param":"keyword"}, 
                {"name":"Яндекс.Картинки", "pattern":"images.yandex", "param":"text"}, 
                {"name":"Яндекс.Mobile", "pattern":"m.yandex", "param":"query"}, 
                {"name":"Яндекс", "pattern":"hghltd.yandex", "param":"text"}, 
                {"name":"Яндекс", "pattern":"yandex", "param":"text"},
                {"name":"УкрНет", "pattern":"ukr.net", "param":"q"},
                {"name":"УкрНет", "pattern":"ukr.net", "param":"q"},
                {"name":"meta", "pattern":"meta.ua", "param":"q"},
                {"name":"findes", "pattern":"findes.com.ua", "param":"q"}, 
                {"name":"webalta", "pattern":"webalta", "param":"q"}, 
                {"name":"bigmir", "pattern":"bigmir.net", "param":"z"}, 
                {"name":"i.ua", "pattern":"i.ua", "param":"q"}, 
                {"name":"online.ua", "pattern":"online.ua", "param":"q"}, 
                {"name":"liveinternet.ru", "pattern":"liveinternet.ru", "param":"q"}, 
                {"name":"all.by", "pattern":"all.by", "param":"query"}
            ];
            var parser = document.createElement('a');
            parser.href = document.referrer;
            for (var i=0; i<search_engines.length; i++)
            {
                if (-1 < parser.hostname.indexOf(search_engines[i]['pattern']))
                {
                    var param = parser.search.replace(new RegExp("\\?",'g'),"").split('&');
                    for (var y=0; y<param.length; y++)
                    {
                        if (param[y].split('=')[0] == search_engines[i]['param'])
                        {
                            result = decodeURIComponent(param[y].split('=')[1]);
                        }
                    }
                }
            }
            return result;
        }""" + u"""
        ;function yottos_windowWidth(){
            var windowWidth = 0;
            if (window.self.innerWidth)
                windowWidth = window.self.innerWidth;
            else if (window.document.documentElement && window.document.documentElement.clientWidth)
                windowWidth = window.document.documentElement.clientWidth;
            else if (window.document.body)
                windowWidth = window.document.body.clientWidth;
            return windowWidth;
        }
        ;function yottos_windowHeight(){
            var windowHeight = 0;
            if (window.self.innerHeight)
                windowHeight = window.self.innerHeight;
            else if (window.document.documentElement && window.document.documentElement.clientHeight)
                windowHeight = window.document.documentElement.clientHeight;
            else if (window.document.body)
                windowHeight = window.document.body.clientHeight;
            return windowHeight;
        }
        ;var rand = Math.floor(Math.random() * 1000000);
        ;var iframe_id = 'yottos' + rand;
        ;var randParam = '&rand=' + rand;
        ;var stats = 'stats';
        ;function yottos_iframe_query(){
            return "?scr=%(guid)s&location=" + encodeURIComponent(window.location.href) + "&w=" + yottos_windowWidth() + "&h=" + yottos_windowHeight() + "&search=" + encodeURIComponent(validate(yottos_getSearch())) + "&context=" + encodeURIComponent(validate(getContext()));
        }
        ;if (typeof(yottos_advertise_div_display) == "undefined")
        {
            ;document.write("<iframe id='" + iframe_id + "' src='http://%(partner)s.rg.yottos.com/adshow.fcgi" + yottos_iframe_query() + randParam + "' width='%(width)s' height='%(height)s'  frameborder='0' scrolling='no'></iframe>");
            if (typeof window[stats] == "undefined")
            {
                ;document.write("<iframe id='stats' src='http://rg.yottos.com/stats.html' width='0' height='0'  frameborder='0' scrolling='no' style='display:none;'></iframe>");
                window[stats] = true;
            }
        }
        else
        {
            ;if (yottos_advertise_div_display == 'none')
            {
                ;document.write("<iframe id='" + iframe_id + "' src='http://%(partner)s.rg.yottos.com/adshow.fcgi" + yottos_iframe_query() + randParam + "' width='%(width)s' height='%(height)s'  frameborder='0' scrolling='no'></iframe>");
                if (typeof window[stats] == "undefined")
                {
                    ;document.write("<iframe src='http://rg.yottos.com/stats.html' width='0' height='0'  frameborder='0' scrolling='no' style='display:none;'></iframe>");
                    window[stats] = true;
                }
            }
            else
            {
                if (document.getElementById(yottos_advertise_div_display) != null)
                {
                    ;document.getElementById(yottos_advertise_div_display).innerHTML = "<iframe id='" + iframe_id + "' src='http://%(partner)s.rg.yottos.com/adshow.fcgi" + yottos_iframe_query() + randParam + "' width='%(width)s' height='%(height)s'  frameborder='0' scrolling='no'></iframe>";
                    if (typeof window[stats] == "undefined")
                    {
                        ;document.write("<iframe src='http://rg.yottos.com/stats.html' width='0' height='0'  frameborder='0' scrolling='no' style='display:none;'></iframe>");
                        window[stats] = true;
                    }
                }
                else
                {
                    ;document.write("<iframe id='" + iframe_id + "' src='http://%(partner)s.rg.yottos.com/adshow.fcgi" + yottos_iframe_query() + randParam + "' width='%(width)s' height='%(height)s'  frameborder='0' scrolling='no'></iframe>");
                    if (typeof window[stats] == "undefined")
                    {
                        ;document.write("<iframe src='http://rg.yottos.com/stats.html' width='0' height='0'  frameborder='0' scrolling='no' style='display:none;'></iframe>");
                        window[stats] = true;
                    }
                }
                delete yottos_advertise_div_display;
            }
        }
        """) % {'partner':partner, 'guid':guid, 'width':width, 'height':height}

    site_id = False
    if site_id:
        piwik_tracker_code = (r"""if(!this.JSON2){this.JSON2={}}(function(){function d(f){return f<10?"0"+f:f}function l(n,m){var f=Object.prototype.toString.apply(n);if(f==="[object Date]"){return isFinite(n.valueOf())?n.getUTCFullYear()+"-"+d(n.getUTCMonth()+1)+"-"+d(n.getUTCDate())+"T"+d(n.getUTCHours())+":"+d(n.getUTCMinutes())+":"+d(n.getUTCSeconds())+"Z":null}if(f==="[object String]"||f==="[object Number]"||f==="[object Boolean]"){return n.valueOf()}if(f!=="[object Array]"&&typeof n.toJSON==="function"){return n.toJSON(m)}return n}var c=new RegExp("[\u0000\u00ad\u0600-\u0604\u070f\u17b4\u17b5\u200c-\u200f\u2028-\u202f\u2060-\u206f\ufeff\ufff0-\uffff]","g"),e='\\\\\\"\x00-\x1f\x7f-\x9f\u00ad\u0600-\u0604\u070f\u17b4\u17b5\u200c-\u200f\u2028-\u202f\u2060-\u206f\ufeff\ufff0-\uffff]',i=new RegExp("["+e,"g"),j,b,k={"\b":"\\b","\t":"\\t","\n":"\\n","\f":"\\f","\r":"\\r",'"':'\\"',"\\":"\\\\"},h;
function a(f){i.lastIndex=0;return i.test(f)?'"'+f.replace(i,function(m){var n=k[m];return typeof n==="string"?n:"\\u"+("0000"+m.charCodeAt(0).toString(16)).slice(-4)})+'"':'"'+f+'"'}function g(s,p){var n,m,t,f,q=j,o,r=p[s];if(r&&typeof r==="object"){r=l(r,s)}if(typeof h==="function"){r=h.call(p,s,r)}switch(typeof r){case"string":return a(r);case"number":return isFinite(r)?String(r):"null";case"boolean":case"null":return String(r);case"object":if(!r){return"null"}j+=b;o=[];if(Object.prototype.toString.apply(r)==="[object Array]"){f=r.length;for(n=0;n<f;n+=1){o[n]=g(n,r)||"null"}t=o.length===0?"[]":j?"[\n"+j+o.join(",\n"+j)+"\n"+q+"]":"["+o.join(",")+"]";j=q;return t}if(h&&typeof h==="object"){f=h.length;for(n=0;n<f;n+=1){if(typeof h[n]==="string"){m=h[n];t=g(m,r);if(t){o.push(a(m)+(j?": ":":")+t)}}}}else{for(m in r){if(Object.prototype.hasOwnProperty.call(r,m)){t=g(m,r);if(t){o.push(a(m)+(j?": ":":")+t)}}}}t=o.length===0?"{}":j?"{\n"+j+o.join(",\n"+j)+"\n"+q+"}":"{"+o.join(",")+"}";j=q;
return t}}if(typeof JSON2.stringify!=="function"){JSON2.stringify=function(o,m,n){var f;j="";b="";if(typeof n==="number"){for(f=0;f<n;f+=1){b+=" "}}else{if(typeof n==="string"){b=n}}h=m;if(m&&typeof m!=="function"&&(typeof m!=="object"||typeof m.length!=="number")){throw new Error("JSON.stringify")}return g("",{"":o})}}if(typeof JSON2.parse!=="function"){JSON2.parse=function(o,f){var n;function m(s,r){var q,p,t=s[r];if(t&&typeof t==="object"){for(q in t){if(Object.prototype.hasOwnProperty.call(t,q)){p=m(t,q);if(p!==undefined){t[q]=p}else{delete t[q]}}}}return f.call(s,r,t)}o=String(o);c.lastIndex=0;if(c.test(o)){o=o.replace(c,function(p){return"\\u"+("0000"+p.charCodeAt(0).toString(16)).slice(-4)})}if((new RegExp("^[\\],:{}\\s]*$")).test(o.replace(new RegExp('\\\\(?:["\\\\/bfnrt]|u[0-9a-fA-F]{4})',"g"),"@").replace(new RegExp('"[^"\\\\\n\r]*"|true|false|null|-?\\d+(?:\\.\\d*)?(?:[eE][+\\-]?\\d+)?',"g"),"]").replace(new RegExp("(?:^|:|,)(?:\\s*\\[)+","g"),""))){n=eval("("+o+")");
return typeof f==="function"?m({"":n},""):n}throw new SyntaxError("JSON.parse")}}}());var _paq=_paq||[],Piwik=Piwik||(function(){var f,a={},p=document,c=navigator,A=screen,x=window,m=false,v=[],h=x.encodeURIComponent,w=x.decodeURIComponent,d=unescape,B,D;function r(i){return typeof i!=="undefined"}function n(i){return typeof i==="function"}function z(i){return typeof i==="object"}function j(i){return typeof i==="string"||i instanceof String}function G(){var L,N,M;for(L=0;L<arguments.length;L+=1){M=arguments[L];N=M.shift();if(j(N)){B[N].apply(B,M)}else{N.apply(B,M)}}}function J(N,M,L,i){if(N.addEventListener){N.addEventListener(M,L,i);return true}if(N.attachEvent){return N.attachEvent("on"+M,L)}N["on"+M]=L}function E(M,P){var L="",O,N;for(O in a){if(Object.prototype.hasOwnProperty.call(a,O)){N=a[O][M];if(n(N)){L+=N(P)}}}return L}function H(){var i;E("unload");if(f){do{i=new Date()}while(i.getTimeAlias()<f)}}function F(){var L;if(!m){m=true;E("load");for(L=0;L<v.length;L++){v[L]()}}return true
}function k(){var L;if(p.addEventListener){J(p,"DOMContentLoaded",function i(){p.removeEventListener("DOMContentLoaded",i,false);F()})}else{if(p.attachEvent){p.attachEvent("onreadystatechange",function i(){if(p.readyState==="complete"){p.detachEvent("onreadystatechange",i);F()}});if(p.documentElement.doScroll&&x===x.top){(function i(){if(!m){try{p.documentElement.doScroll("left")}catch(M){setTimeout(i,0);return}F()}}())}}}if((new RegExp("WebKit")).test(c.userAgent)){L=setInterval(function(){if(m||/loaded|complete/.test(p.readyState)){clearInterval(L);F()}},10)}J(x,"load",F,false)}function s(){var i="";try{i=x.top.document.referrer}catch(M){if(x.parent){try{i=x.parent.document.referrer}catch(L){i=""}}}if(i===""){i=p.referrer}return i}function g(i){var M=new RegExp("^([a-z]+):"),L=M.exec(i);return L?L[1]:null}function b(i){var M=new RegExp("^(?:(?:https?|ftp):)/*(?:[^@]+@)?([^:/#]+)"),L=M.exec(i);return L?L[1]:i}function y(M,L){var P=new RegExp("^(?:https?|ftp)(?::/*(?:[^?]+)[?])([^#]+)"),O=P.exec(M),N=new RegExp("(?:^|&)"+L+"=([^&]*)"),i=O?N.exec(O[1]):0;
return i?w(i[1]):""}function l(Q,N,M,P,L,O){var i;if(M){i=new Date();i.setTime(i.getTime()+M)}p.cookie=Q+"="+h(N)+(M?";expires="+i.toGMTString():"")+";path="+(P||"/")+(L?";domain="+L:"")+(O?";secure":"")}function e(M){var i=new RegExp("(^|;)[ ]*"+M+"=([^;]*)"),L=i.exec(p.cookie);return L?w(L[2]):0}function o(i){return d(h(i))}function I(ab){var N=function(W,i){return(W<<i)|(W>>>(32-i))},ac=function(ai){var ah="",ag,W;for(ag=7;ag>=0;ag--){W=(ai>>>(ag*4))&15;ah+=W.toString(16)}return ah},Q,ae,ad,M=[],U=1732584193,S=4023233417,R=2562383102,P=271733878,O=3285377520,aa,Z,Y,X,V,af,L,T=[];ab=o(ab);L=ab.length;for(ae=0;ae<L-3;ae+=4){ad=ab.charCodeAt(ae)<<24|ab.charCodeAt(ae+1)<<16|ab.charCodeAt(ae+2)<<8|ab.charCodeAt(ae+3);T.push(ad)}switch(L&3){case 0:ae=2147483648;break;case 1:ae=ab.charCodeAt(L-1)<<24|8388608;break;case 2:ae=ab.charCodeAt(L-2)<<24|ab.charCodeAt(L-1)<<16|32768;break;case 3:ae=ab.charCodeAt(L-3)<<24|ab.charCodeAt(L-2)<<16|ab.charCodeAt(L-1)<<8|128;break}T.push(ae);while((T.length&15)!==14){T.push(0)
}T.push(L>>>29);T.push((L<<3)&4294967295);for(Q=0;Q<T.length;Q+=16){for(ae=0;ae<16;ae++){M[ae]=T[Q+ae]}for(ae=16;ae<=79;ae++){M[ae]=N(M[ae-3]^M[ae-8]^M[ae-14]^M[ae-16],1)}aa=U;Z=S;Y=R;X=P;V=O;for(ae=0;ae<=19;ae++){af=(N(aa,5)+((Z&Y)|(~Z&X))+V+M[ae]+1518500249)&4294967295;V=X;X=Y;Y=N(Z,30);Z=aa;aa=af}for(ae=20;ae<=39;ae++){af=(N(aa,5)+(Z^Y^X)+V+M[ae]+1859775393)&4294967295;V=X;X=Y;Y=N(Z,30);Z=aa;aa=af}for(ae=40;ae<=59;ae++){af=(N(aa,5)+((Z&Y)|(Z&X)|(Y&X))+V+M[ae]+2400959708)&4294967295;V=X;X=Y;Y=N(Z,30);Z=aa;aa=af}for(ae=60;ae<=79;ae++){af=(N(aa,5)+(Z^Y^X)+V+M[ae]+3395469782)&4294967295;V=X;X=Y;Y=N(Z,30);Z=aa;aa=af}U=(U+aa)&4294967295;S=(S+Z)&4294967295;R=(R+Y)&4294967295;P=(P+X)&4294967295;O=(O+V)&4294967295}af=ac(U)+ac(S)+ac(R)+ac(P)+ac(O);return af.toLowerCase()}function C(M,i,L){if(M==="translate.googleusercontent.com"){if(L===""){L=i}i=y(i,"u");M=b(i)}else{if(M==="cc.bingj.com"||M==="webcache.googleusercontent.com"||M.slice(0,5)==="74.6."){i=p.links[0].href;M=b(i)}}return[M,i,L]}function t(L){var i=L.length;
if(L.charAt(--i)==="."){L=L.slice(0,i)}if(L.slice(0,2)==="*."){L=L.slice(1)}return L}function K(L){if(!j(L)){L=L.text||"";var i=p.getElementsByTagName("title");if(i&&r(i[0])){L=i[0].text}}return L}function u(ad,aB){var O=C(p.domain,x.location.href,s()),aT=t(O[0]),a7=O[1],aH=O[2],aF="GET",N=ad||"",aX=aB||"",ar,ai=p.title,ak="7z|aac|ar[cj]|as[fx]|avi|bin|csv|deb|dmg|doc|exe|flv|gif|gz|gzip|hqx|jar|jpe?g|js|mp(2|3|4|e?g)|mov(ie)?|ms[ip]|od[bfgpst]|og[gv]|pdf|phps|png|ppt|qtm?|ra[mr]?|rpm|sea|sit|tar|t?bz2?|tgz|torrent|txt|wav|wm[av]|wpd||xls|xml|z|zip",aD=[aT],R=[],aw=[],ac=[],aC=500,S,ae,T,U,am=["pk_campaign","piwik_campaign","utm_campaign","utm_source","utm_medium"],ah=["pk_kwd","piwik_kwd","utm_term"],a5="_pk_",W,a6,a0,ao,aq,aa=63072000000,ab=1800000,at=15768000000,Z=p.location.protocol==="https",Q=false,ax={},a1=200,aN={},aY={},aK=false,aI=false,aG,ay,X,al=I,aJ,ap;function a2(ba){var bb;if(T){bb=new RegExp("#.*");return ba.replace(bb,"")}return ba}function aS(bc,ba){var bd=g(ba),bb;if(bd){return ba
}if(ba.slice(0,1)==="/"){return g(bc)+"://"+b(bc)+ba}bc=a2(bc);if((bb=bc.indexOf("?"))>=0){bc=bc.slice(0,bb)}if((bb=bc.lastIndexOf("/"))!==bc.length-1){bc=bc.slice(0,bb+1)}return bc+ba}function aE(bd){var bb,ba,bc;for(bb=0;bb<aD.length;bb++){ba=t(aD[bb].toLowerCase());if(bd===ba){return true}if(ba.slice(0,1)==="."){if(bd===ba.slice(1)){return true}bc=bd.length-ba.length;if((bc>0)&&(bd.slice(bc)===ba)){return true}}}return false}function a9(ba){var bb=new Image(1,1);bb.onload=function(){};bb.src=N+(N.indexOf("?")<0?"?":"&")+ba}function aP(ba){try{var bc=x.XDomainRequest?new x.XDomainRequest():x.XMLHttpRequest?new x.XMLHttpRequest():x.ActiveXObject?new ActiveXObject("Microsoft.XMLHTTP"):null;bc.open("POST",N,true);bc.onreadystatechange=function(){if(this.readyState===4&&this.status!==200){a9(ba)}};bc.setRequestHeader("Content-Type","application/x-www-form-urlencoded; charset=UTF-8");bc.send(ba)}catch(bb){a9(ba)}}function an(bc,bb){var ba=new Date();if(!a0){if(aF==="POST"){aP(bc)}else{a9(bc)
}f=ba.getTime()+bb}}function aO(ba){return a5+ba+"."+aX+"."+aJ}function P(){var ba=aO("testcookie");if(!r(c.cookieEnabled)){l(ba,"1");return e(ba)==="1"?"1":"0"}return c.cookieEnabled?"1":"0"}function az(){aJ=al((W||aT)+(a6||"/")).slice(0,4)}function Y(){var bb=aO("cvar"),ba=e(bb);if(ba.length){ba=JSON2.parse(ba);if(z(ba)){return ba}}return{}}function M(){if(Q===false){Q=Y()}}function aW(){var ba=new Date();aG=ba.getTime()}function V(be,bb,ba,bd,bc,bf){l(aO("id"),be+"."+bb+"."+ba+"."+bd+"."+bc+"."+bf,aa,a6,W,Z)}function L(){var bb=new Date(),ba=Math.round(bb.getTime()/1000),bd=e(aO("id")),bc;if(bd){bc=bd.split(".");bc.unshift("0")}else{if(!ap){ap=al((c.userAgent||"")+(c.platform||"")+JSON2.stringify(aY)+ba).slice(0,16)}bc=["1",ap,ba,0,ba,"",""]}return bc}function i(){var ba=e(aO("ref"));if(ba.length){try{ba=JSON2.parse(ba);if(z(ba)){return ba}}catch(bb){}}return["","",0,""]}function aj(bc,bA,bB,be){var by,bb=new Date(),bk=Math.round(bb.getTime()/1000),bD,bz,bg,br,bv,bj,bt,bh,bx,bf=1024,bE,bn,bu=Q,bp=aO("id"),bl=aO("ses"),bm=aO("ref"),bF=aO("cvar"),bs=L(),bo=e(bl),bw=i(),bC=ar||a7,bi,ba;
if(a0){l(bp,"",-1,a6,W);l(bl,"",-1,a6,W);l(bF,"",-1,a6,W);l(bm,"",-1,a6,W);return""}bD=bs[0];bz=bs[1];br=bs[2];bg=bs[3];bv=bs[4];bj=bs[5];if(!r(bs[6])){bs[6]=""}bt=bs[6];if(!r(be)){be=""}bi=bw[0];ba=bw[1];bh=bw[2];bx=bw[3];if(!bo){bg++;bj=bv;if(!aq||!bi.length){for(by in am){if(Object.prototype.hasOwnProperty.call(am,by)){bi=y(bC,am[by]);if(bi.length){break}}}for(by in ah){if(Object.prototype.hasOwnProperty.call(ah,by)){ba=y(bC,ah[by]);if(ba.length){break}}}}bE=b(aH);bn=bx.length?b(bx):"";if(bE.length&&!aE(bE)&&(!aq||!bn.length||aE(bn))){bx=aH}if(bx.length||bi.length){bh=bk;bw=[bi,ba,bh,a2(bx.slice(0,bf))];l(bm,JSON2.stringify(bw),at,a6,W,Z)}}bc+="&idsite="+aX+"&rec=1&r="+String(Math.random()).slice(2,8)+"&h="+bb.getHours()+"&m="+bb.getMinutes()+"&s="+bb.getSeconds()+"&url="+h(a2(bC))+(aH.length?"&urlref="+h(a2(aH)):"")+"&_id="+bz+"&_idts="+br+"&_idvc="+bg+"&_idn="+bD+(bi.length?"&_rcn="+h(bi):"")+(ba.length?"&_rck="+h(ba):"")+"&_refts="+bh+"&_viewts="+bj+(String(bt).length?"&_ects="+bt:"")+(String(bx).length?"&_ref="+h(a2(bx.slice(0,bf))):"");
var bd=JSON2.stringify(ax);if(bd.length>2){bc+="&cvar="+h(bd)}for(by in aY){if(Object.prototype.hasOwnProperty.call(aY,by)){bc+="&"+by+"="+aY[by]}}if(bA){bc+="&data="+h(JSON2.stringify(bA))}else{if(U){bc+="&data="+h(JSON2.stringify(U))}}if(Q){var bq=JSON2.stringify(Q);if(bq.length>2){bc+="&_cvar="+h(bq)}for(by in bu){if(Object.prototype.hasOwnProperty.call(bu,by)){if(Q[by][0]===""||Q[by][1]===""){delete Q[by]}}}l(bF,JSON2.stringify(Q),ab,a6,W,Z)}V(bz,br,bg,bk,bj,r(be)&&String(be).length?be:bt);l(bl,"*",ab,a6,W,Z);bc+=E(bB);return bc}function aR(bd,bc,bh,be,ba,bk){var bf="idgoal=0",bg,bb=new Date(),bi=[],bj;if(String(bd).length){bf+="&ec_id="+h(bd);bg=Math.round(bb.getTime()/1000)}bf+="&revenue="+bc;if(String(bh).length){bf+="&ec_st="+bh}if(String(be).length){bf+="&ec_tx="+be}if(String(ba).length){bf+="&ec_sh="+ba}if(String(bk).length){bf+="&ec_dt="+bk}if(aN){for(bj in aN){if(Object.prototype.hasOwnProperty.call(aN,bj)){if(!r(aN[bj][1])){aN[bj][1]=""}if(!r(aN[bj][2])){aN[bj][2]=""}if(!r(aN[bj][3])||String(aN[bj][3]).length===0){aN[bj][3]=0
}if(!r(aN[bj][4])||String(aN[bj][4]).length===0){aN[bj][4]=1}bi.push(aN[bj])}}bf+="&ec_items="+h(JSON2.stringify(bi))}bf=aj(bf,U,"ecommerce",bg);an(bf,aC)}function aQ(ba,be,bd,bc,bb,bf){if(String(ba).length&&r(be)){aR(ba,be,bd,bc,bb,bf)}}function a4(ba){if(r(ba)){aR("",ba,"","","","")}}function av(bd,be){var ba=new Date(),bc=aj("action_name="+h(K(bd||ai)),be,"log");an(bc,aC);if(S&&ae&&!aI){aI=true;J(p,"click",aW);J(p,"mouseup",aW);J(p,"mousedown",aW);J(p,"mousemove",aW);J(p,"mousewheel",aW);J(x,"DOMMouseScroll",aW);J(x,"scroll",aW);J(p,"keypress",aW);J(p,"keydown",aW);J(p,"keyup",aW);J(x,"resize",aW);J(x,"focus",aW);J(x,"blur",aW);aG=ba.getTime();setTimeout(function bb(){var bf=new Date(),bg;if((aG+ae)>bf.getTime()){if(S<bf.getTime()){bg=aj("ping=1",be,"ping");an(bg,aC)}setTimeout(bb,ae)}},ae)}}function aA(ba,bd,bc){var bb=aj("idgoal="+ba+(bd?"&revenue="+bd:""),bc,"goal");an(bb,aC)}function aV(bb,ba,bd){var bc=aj(ba+"="+h(a2(bb)),bd,"link");an(bc,aC)}function aZ(bb,ba){if(bb!==""){return bb+ba.charAt(0).toUpperCase()+ba.slice(1)
}return ba}function ag(bf){var be,ba,bd=["","webkit","ms","moz"],bc;if(!ao){for(ba=0;ba<bd.length;ba++){bc=bd[ba];if(Object.prototype.hasOwnProperty.call(p,aZ(bc,"hidden"))){if(p[aZ(bc,"visibilityState")]==="prerender"){be=true}break}}}if(be){J(p,bc+"visibilitychange",function bb(){p.removeEventListener(bc+"visibilitychange",bb,false);bf()});return}bf()}function af(bc,bb){var bd,ba="(^| )(piwik[_-]"+bb;if(bc){for(bd=0;bd<bc.length;bd++){ba+="|"+bc[bd]}}ba+=")( |$)";return new RegExp(ba)}function aU(bd,ba,be){if(!be){return"link"}var bc=af(aw,"download"),bb=af(ac,"link"),bf=new RegExp("\\.("+ak+")([?&#]|$)","i");return bb.test(bd)?"link":(bc.test(bd)||bf.test(ba)?"download":0)}function aM(bf){var bd,bb,ba;while((bd=bf.parentNode)!==null&&r(bd)&&((bb=bf.tagName.toUpperCase())!=="A"&&bb!=="AREA")){bf=bd}if(r(bf.href)){var bg=bf.hostname||b(bf.href),bh=bg.toLowerCase(),bc=bf.href.replace(bg,bh),be=new RegExp("^(javascript|vbscript|jscript|mocha|livescript|ecmascript|mailto):","i");if(!be.test(bc)){ba=aU(bf.className,bc,aE(bh));
if(ba){bc=d(bc);aV(bc,ba)}}}}function a8(ba){var bb,bc;ba=ba||x.event;bb=ba.which||ba.button;bc=ba.target||ba.srcElement;if(ba.type==="click"){if(bc){aM(bc)}}else{if(ba.type==="mousedown"){if((bb===1||bb===2)&&bc){ay=bb;X=bc}else{ay=X=null}}else{if(ba.type==="mouseup"){if(bb===ay&&bc===X){aM(bc)}ay=X=null}}}}function aL(bb,ba){if(ba){J(bb,"mouseup",a8,false);J(bb,"mousedown",a8,false)}else{J(bb,"click",a8,false)}}function au(bb){if(!aK){aK=true;var bc,ba=af(R,"ignore"),bd=p.links;if(bd){for(bc=0;bc<bd.length;bc++){if(!ba.test(bd[bc].className)){aL(bd[bc],bb)}}}}}function a3(){var ba,bb,bc={pdf:"application/pdf",qt:"video/quicktime",realp:"audio/x-pn-realaudio-plugin",wma:"application/x-mplayer2",dir:"application/x-director",fla:"application/x-shockwave-flash",java:"application/x-java-vm",gears:"application/x-googlegears",ag:"application/x-silverlight"};if(c.mimeTypes&&c.mimeTypes.length){for(ba in bc){if(Object.prototype.hasOwnProperty.call(bc,ba)){bb=c.mimeTypes[bc[ba]];aY[ba]=(bb&&bb.enabledPlugin)?"1":"0"
}}}if(typeof navigator.javaEnabled!=="unknown"&&r(c.javaEnabled)&&c.javaEnabled()){aY.java="1"}if(n(x.GearsFactory)){aY.gears="1"}aY.res=A.width+"x"+A.height;aY.cookie=P()}a3();az();return{getVisitorId:function(){return(L())[1]},getVisitorInfo:function(){return L()},getAttributionInfo:function(){return i()},getAttributionCampaignName:function(){return i()[0]},getAttributionCampaignKeyword:function(){return i()[1]},getAttributionReferrerTimestamp:function(){return i()[2]},getAttributionReferrerUrl:function(){return i()[3]},setTrackerUrl:function(ba){N=ba},setSiteId:function(ba){aX=ba},setCustomData:function(ba,bb){if(z(ba)){U=ba}else{if(!U){U=[]}U[ba]=bb}},getCustomData:function(){return U},setCustomVariable:function(bb,ba,be,bc){var bd;if(!r(bc)){bc="visit"}if(bb>0){ba=r(ba)&&!j(ba)?String(ba):ba;be=r(be)&&!j(be)?String(be):be;bd=[ba.slice(0,a1),be.slice(0,a1)];if(bc==="visit"||bc===2){M();Q[bb]=bd}else{if(bc==="page"||bc===3){ax[bb]=bd}}}},getCustomVariable:function(bb,bc){var ba;if(!r(bc)){bc="visit"
}if(bc==="page"||bc===3){ba=ax[bb]}else{if(bc==="visit"||bc===2){M();ba=Q[bb]}}if(!r(ba)||(ba&&ba[0]==="")){return false}return ba},deleteCustomVariable:function(ba,bb){if(this.getCustomVariable(ba,bb)){this.setCustomVariable(ba,"","",bb)}},setLinkTrackingTimer:function(ba){aC=ba},setDownloadExtensions:function(ba){ak=ba},addDownloadExtensions:function(ba){ak+="|"+ba},setDomains:function(ba){aD=j(ba)?[ba]:ba;aD.push(aT)},setIgnoreClasses:function(ba){R=j(ba)?[ba]:ba},setRequestMethod:function(ba){aF=ba||"GET"},setReferrerUrl:function(ba){aH=ba},setCustomUrl:function(ba){ar=aS(a7,ba)},setDocumentTitle:function(ba){ai=ba},setDownloadClasses:function(ba){aw=j(ba)?[ba]:ba},setLinkClasses:function(ba){ac=j(ba)?[ba]:ba},setCampaignNameKey:function(ba){am=j(ba)?[ba]:ba},setCampaignKeywordKey:function(ba){ah=j(ba)?[ba]:ba},discardHashTag:function(ba){T=ba},setCookieNamePrefix:function(ba){a5=ba;Q=Y()},setCookieDomain:function(ba){W=t(ba);az()},setCookiePath:function(ba){a6=ba;az()},setVisitorCookieTimeout:function(ba){aa=ba*1000
},setSessionCookieTimeout:function(ba){ab=ba*1000},setReferralCookieTimeout:function(ba){at=ba*1000},setConversionAttributionFirstReferrer:function(ba){aq=ba},setDoNotTrack:function(bb){var ba=c.doNotTrack||c.msDoNotTrack;a0=bb&&(ba==="yes"||ba==="1")},addListener:function(bb,ba){aL(bb,ba)},enableLinkTracking:function(ba){if(m){au(ba)}else{v.push(function(){au(ba)})}},setHeartBeatTimer:function(bc,bb){var ba=new Date();S=ba.getTime()+bc*1000;ae=bb*1000},killFrame:function(){if(x.location!==x.top.location){x.top.location=x.location}},redirectFile:function(ba){if(x.location.protocol==="file:"){x.location=ba}},setCountPreRendered:function(ba){ao=ba},trackGoal:function(ba,bc,bb){ag(function(){aA(ba,bc,bb)})},trackLink:function(bb,ba,bc){ag(function(){aV(bb,ba,bc)})},trackPageView:function(ba,bb){ag(function(){av(ba,bb)})},setEcommerceView:function(bd,ba,bc,bb){if(!r(bc)||!bc.length){bc=""}else{if(bc instanceof Array){bc=JSON2.stringify(bc)}}ax[5]=["_pkc",bc];if(r(bb)&&String(bb).length){ax[2]=["_pkp",bb]
}if((!r(bd)||!bd.length)&&(!r(ba)||!ba.length)){return}if(r(bd)&&bd.length){ax[3]=["_pks",bd]}if(!r(ba)||!ba.length){ba=""}ax[4]=["_pkn",ba]},addEcommerceItem:function(be,ba,bc,bb,bd){if(be.length){aN[be]=[be,ba,bc,bb,bd]}},trackEcommerceOrder:function(ba,be,bd,bc,bb,bf){aQ(ba,be,bd,bc,bb,bf)},trackEcommerceCartUpdate:function(ba){a4(ba)}}}function q(){return{push:G}}J(x,"beforeunload",H,false);k();Date.prototype.getTimeAlias=Date.prototype.getTime;B=new u();for(D=0;D<_paq.length;D++){G(_paq[D])}_paq=new q();return{addPlugin:function(i,L){a[i]=L},getTracker:function(i,L){return new u(i,L)},getAsyncTracker:function(){return B}}}()),piwik_track,piwik_log=function(b,f,d,g){function a(h){try{return eval("piwik_"+h)}catch(i){}return}var c,e=Piwik.getTracker(d,f);e.setDocumentTitle(b);e.setCustomData(g);c=a("tracker_pause");if(c){e.setLinkTrackingTimer(c)}c=a("download_extensions");if(c){e.setDownloadExtensions(c)}c=a("hosts_alias");if(c){e.setDomains(c)}c=a("ignore_classes");if(c){e.setIgnoreClasses(c)
}e.trackPageView();if(a("install_tracker")){piwik_track=function(i,k,j,h){e.setSiteId(k);e.setTrackerUrl(j);e.trackLink(i,h)};e.enableLinkTracking()}}; var pkBaseURL = (("https:" == document.location.protocol) ? "https://attractor.yottos.com/" : "http://attractor.yottos.com/");try{var piwikTracker = Piwik.getTracker(pkBaseURL + "piwik.php", %(piwik_site_id)s);piwikTracker.trackPageView();piwikTracker.enableLinkTracking();} catch (err) {}""") % {'piwik_site_id': str(site_id)}
        return """//<![CDATA[\n""" + minifier.minify(script, mangle=False) + piwik_tracker_code + """\n//]]>"""
    return """//<![CDATA[\n""" + minifier.minify(script.encode('utf-8'), mangle=False) + """\n//]]>"""
    #return """//<![CDATA[\n""" + script.encode('utf-8') + """\n//]]>"""


def upload_all():
    # Параметры FTP для заливки загрузчиков информеров
    informer_loader_ftp = '213.186.121.76'
    informer_loader_ftp_user = 'cdn'
    informer_loader_ftp_password = '$www-app$'
    informer_loader_ftp_path = 'httpdocs/getmyad'
    db = pymongo.Connection(host='yottos.ru,213.186.121.76:27018,213.186.121.199:27018').getmyad_db
    ftp = FTP(host=informer_loader_ftp,
              user=informer_loader_ftp_user,
              passwd=informer_loader_ftp_password)
    ftp.cwd(informer_loader_ftp_path)
    
    informers = [x['guid'] for x in db.informer.find({}, ['guid'])]
    informers += map(lambda x: x.upper(), informers)        # Для тех, кому выдавался upper-case GUID
    
    for informer in informers:
        print "Uploading %s" % informer
        loader = StringIO.StringIO()
        loader.write(_generate_informer_loader(informer))
        loader.seek(0)
        ftp.storlines('STOR %s.js' % informer, loader)

    #informer = '3bfe6280-1b8f-11e1-ae13-00163e0300c1'
    #loader = StringIO.StringIO()
    #loader.write(_generate_informer_loader(informer))
    #loader.seek(0)
    #ftp.storlines('STOR %s.js' % informer, loader)

    
    ftp.quit()
    loader.close()
    

if __name__ == '__main__':
    upload_all()
    print "Finished!"
    exit()
    
