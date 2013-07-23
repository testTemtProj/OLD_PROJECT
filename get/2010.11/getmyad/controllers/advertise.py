# This Python file uses the following encoding: utf-8
from datetime import datetime
from getmyad.lib.base import BaseController, render
from getmyad.model import allAdvertiseScriptsSummary, statGroupedByDate
from pylons import request, response, session, tmpl_context as c, url, \
    app_globals, config
from pylons.controllers.util import abort, redirect
from routes.util import url_for
import getmyad.lib.helpers as h
import getmyad.model as model
import json
import logging
import pymongo.json_util
import re
import time


#from getmyad.other.upload_scripts import InformerUploader

log = logging.getLogger(__name__)

def dateFromStr(str):
    try:
        day = int(str[0:2])
        month = int(str[3:5])
        year = int(str[6:10])
        return datetime(year, month, day)
    except:
        return None
html_re = re.compile(" /^<([a-z]+)([^>]+)*(?:>(.*)<\/\1>|\s+\/>)$/")
def validdate_size(size):
    size_re = re.compile(" /^?([0-9]{4})$/")
    if re.match(html_re, size):
        return False
    else:
        if re.match(size_re, size):
            return size
        else:
            return False
    
    
def validate_color(color):
    color_re = re.compile(r"/^#?([a-f0-9]{6}|[a-f0-9]{3})$/")
    if re.match(html_re, color):
        return False
    else:
        if re.match(color_re, color):
            return color
        else:
            return False
     
# "констаты" для конвертации чисел
BASE2 = "01"
#BASE8 = "01234567"
BASE10 = "0123456789"
BASE16 = "0123456789ABCDEF"
#BASE62 = "ABCDEFGHIJKLMNOPQRSTUVWXYZ0123456789abcdefghijklmnopqrstuvwxyz"

def baseconvert(number, fromdigits, todigits):
    """
    конвертация чисел 
    """
    if str(number)[0] == '-':
        number = str(number)[1:]
        neg = 1
    else:
        neg = 0

    # make an integer out of the number
    x = long(0)
    for digit in str(number):
        x = x * len(fromdigits) + fromdigits.index(digit)
    
    # create the result in base 'len(todigits)'
    res = ""
    while x > 0:
        digit = x % len(todigits)
        res = todigits[digit] + res
        x /= len(todigits)
    if neg:
        res = "-" + res

    return res


def dec2hex(i):
    return baseconvert(i, BASE10, BASE16)

def hex2dec(i):
    return baseconvert(i, BASE16, BASE10)

def rgb(r , g , b):
    return dec2hex(int(r)) + dec2hex(int(g)) + dec2hex(int(b))

def adv_to_css(opt):
    u"""
    Создает строку CSS из параметров Admaker
    """

    try:
        DescriptionHide = ""                
        if  str(opt['Description']['hide']) == 'True':
            DescriptionHide = "\n\tdisplay: none;"
        DescriptionWidth = str(opt['Description']['width'])        
        DescriptionHeight = str(opt['Description']['height'])
        DescriptionBorderWidth = str(opt['Description']['borderWidth'])
        DescriptionBorderColor = str(opt['Description']['borderColor'])
        DescriptionFontUnderline = str(opt['Description']['fontUnderline'])
        DescriptionFontBold = str(opt['Description']['fontBold'])
        DescriptionFontColor = str(opt['Description']['fontColor'])
        try:
            DescriptionFontSize = str(opt['Description']['fontSize'])            
        except:
            DescriptionFontSize = "10"
        try:
            DescriptionFontFamily = str(opt['Description']['fontFamily'])
        except:
            DescriptionFontFamily = 'Arial, "Helvetica CY",  sans-serif;'
        #DescriptionHide = str(opt['Description']['hide'])
        DescriptionTop = str(opt['Description']['top'])
        try:
            DescriptionAlign = str(opt['Description']['align'])
        except:
            DescriptionAlign = 'center'
        DescriptionLeft = str(opt['Description']['left'])
        #DescriptionBackgroundColor = str(opt['Description']['backgroundColor'])
        mainWidth = str(opt['Main']['width'])
        mainHeight = str(opt['Main']['height'])
        mainBorderWidth = str(opt['Main']['borderWidth'])
        mainBorderColor = str(opt['Main']['borderColor'])
        mainFontUnderline = str(opt['Main']['fontUnderline'])
        mainFontBold = str(opt['Main']['fontBold'])
        try:
            mainFontFamily = str(opt['Main']['fontFamily'])
        except:
            mainFontFamily = 'Arial, "Helvetica CY",  sans-serif;'
        mainHide = str(opt['Main']['hide'])
        mainTop = str(opt['Main']['top'])
        mainBackgroundColor = str(opt['Main']['backgroundColor'])
        try:
            mainAlign = str(opt['Main']['align'])
        except:
            mainAlign = 'center'
        mainLeft = str(opt['Main']['left'])
        #Image
        ImageWidth = str(opt['Image']['width'])
        ImageHeight = str(opt['Image']['height'])
        ImageBorderWidth = str(opt['Image']['borderWidth']) or "0"
        ImageBorderColor = str(opt['Image']['borderColor'])
        ImageFontUnderline = str(opt['Image']['fontUnderline'])
        ImageFontBold = str(opt['Image']['fontBold'])
        #ImageFontFamily = str(opt['Image']['fontFamily'])
        ImageHide = str(opt['Image']['hide'])
        ImageTop = str(opt['Image']['top'])
        #ImageBackgroundColor = str(opt['Image']['backgroundColor'])
        #ImageAlign = str(opt['Image']['align'])
        ImageLeft = str(opt['Image']['left'])
        #Header
        HeaderWidth = str(opt['Header']['width'])
        HeaderHeight = str(opt['Header']['height'])
        HeaderBorderWidth = str(opt['Header']['borderWidth'])
        HeaderBorderColor = str(opt['Header']['borderColor'])
        HeaderFontUnderline = str(opt['Header']['fontUnderline'])
        HeaderFontBold = str(opt['Header']['fontBold'])
        try:
            HeaderFontColor = str(opt['Header']['fontColor'])
        except:
            HeaderFontColor = "7777CC"
        try:
            HeaderFontSize = str(opt['Header']['fontSize'])
        except:
            HeaderFontSize = "10"
        try:
            HeaderFontFamily = str(opt['Header']['fontFamily'])
        except:
            HeaderFontFamily = 'Arial, "Helvetica CY",  sans-serif;'
        HeaderHide = str(opt['Header']['hide'])
        HeaderTop = str(opt['Header']['top'])
        try:                    
            HeaderAlign = str(opt['Header']['align'])            
        except:
            HeaderAlign = 'center'
        HeaderLeft = str(opt['Header']['left'])
        #cost
        CostWidth = str(opt['Cost']['width'])
        CostHide = ""
        if str(opt['Cost']['hide']) == 'True':
            CostHide = "\n\tdisplay: none;"
        CostHeight = str(opt['Cost']['height'])
        CostBorderWidth = str(opt['Cost']['borderWidth'])
        CostBorderColor = str(opt['Cost']['borderColor'])
        CostFontUnderline = str(opt['Cost']['fontUnderline'])
        CostFontBold = str(opt['Cost']['fontBold'])
        CostFontColor = str(opt['Cost']['fontColor'])
        try:
            CostFontSize = str(opt['Cost']['fontSize'])
        except:
            CostFontSize = "13" 
        try:
            CostFontFamily = str(opt['Cost']['fontFamily'])
        except:
            CostFontFamily = 'Arial, "Helvetica CY",  sans-serif;'        
        CostTop = str(opt['Cost']['top'])
        try:
            CostAlign = str(opt['Cost']['align'])
        except:
            CostAlign = 'center'
        CostLeft = str(opt['Cost']['left'])
        #Nav 
        NavColor = str(opt['Nav']['color'])
        NavLogoPosition = str(opt['Nav']['logoPosition'])
        NavLogoColor = str(opt['Nav']['logoColor'])
        NavColor = str(opt['Nav']['color'])
        NavPosition = str(opt['Nav']['navPosition'])
        NavBackgroundColor = str(opt['Nav']['backgroundColor'])
        #
        advWidth = str(opt['Advertise']['width'])                
        advHeight = str(opt['Advertise']['height'])
        advBorderWidth = str(opt['Advertise']['borderWidth'])
        advBorderColor = str(opt['Advertise']['borderColor'])
        advFontUnderline = str(opt['Advertise']['fontUnderline'])
        advFontBold = str(opt['Advertise']['fontBold'])
        try:
            advFontFamily = str(opt['Advertise']['fontFamily'])
        except:
            advFontFamily = 'Arial, "Helvetica CY",  sans-serif;'
        advHide = str(opt['Advertise']['hide'])
        advTop = str(opt['Advertise']['top'])
        try: 
            advAlign = str(opt['Advertise']['align'])
        except:
            advAlign = 'center'
        advLeft = str(opt['Advertise']['left'])
        
         
        css = u"""
<style type="text/css">
#mainContainer {
    position: relative;
    width: %s;
    height: %s;
    border: %spx solid #%s;
    background-color: #%s;
    overflow: hidden;
    border-radius: 5px;
}
        """ % (
            mainWidth,
            mainHeight,
            mainBorderWidth,
            mainBorderColor,
            mainBackgroundColor,
            )
        
        css = css + u"""
.advBlock {
    width: %s;
    height: %s;
    border: %spx solid #%s;
    float: left;
    position: relative;
    font-family: %s
    color: #;
    overflow: hidden;
}""" % (
      advWidth,
      advHeight,
      advBorderWidth,
      advBorderColor,
      advFontFamily
      )
    
        css = css + u"""
.advHeader {
    position: absolute;
    top: %spx;
    left:%spx;
    width: %s;
    height:%s;
    border:  %spx solid #%s;
    overflow: hidden;
    text-align: %s;

    }""" % (
              HeaderTop,
              HeaderLeft,
              HeaderWidth,
              HeaderHeight,
              HeaderBorderWidth,
              HeaderBorderColor,
              HeaderAlign                         
        )
        
        css = css + u"""
.advHeader, .advHeader:hover, .advHeader:visited, .advHeader:active, .advHeader:link {
    text-decoration: none;
    color: #%s;
    font-size: %spx;
    font-weight: bold;
}""" % (HeaderFontColor,
      HeaderFontSize
      )


        css = css + u"""
.advHeader:hover {
    text-decoration: underline;
}


.advDescription {
    position: absolute;
    top: %spx;
    left: %spx;
    width: %s;
    height: %s;
    border:  %spx solid #%s;
    overflow: hidden;        
    text-align: %s;%s
}""" % (
        DescriptionTop,
        DescriptionLeft,
        DescriptionWidth,
        DescriptionHeight,
        DescriptionBorderWidth,
        DescriptionBorderColor,
        DescriptionAlign,
        DescriptionHide
       )
        
        css = css + u"""
.advDescription, .advDescription:hover, .advDescription:visited, .advDescription:active, .advDescription:link {
    text-decoration: none;
    color: #%s;
    font-size: %spx;
    font-family:%s
}""" % (
      DescriptionFontColor,
      DescriptionFontSize,
      DescriptionFontFamily
     )
        css = css + u"""        
.advDescription:hover {
    text-decoration: underline;
}
    """
        css = css + u"""
.advCost {
    position: absolute;
    top: %spx;
    left: %spx;
    width: %s;
    height: %s;
    border: %spx solid #%s;
    overflow: hidden;
    text-align: %s;
}

.advCost, .advCost:link, .advCost:hover, .advCost:visited, .advCost:active {
    text-decoration: none;
    color: #%s;
    font-size: %spx;
    font-family:%s;
    font-weight: bold;%s
}

.advCost:hover {
    text-decoration: underline;
}""" % (
              CostTop,
            CostLeft,
            CostWidth,
            CostHeight,
            CostBorderWidth,
            CostBorderColor,
            CostAlign,
            CostFontColor,
            CostFontSize,
            CostFontFamily,
            CostHide
          )
        css = css + u"""
.advImage {
    position: absolute;
    width: %s;
    height: %s;
    top: %spx;
    left: %spx;
    border: %spx solid #%s;
}
    """ % (
        ImageWidth,
        ImageHeight,
        ImageTop,
        ImageLeft,
        ImageBorderWidth,
        ImageBorderColor    
        )
        #return NavPosition
        NavTop = ""        
        NavLeft = ""
        NavBottom = ""
        NavRight = ""        
        NavLeftR = ""        
        NavRightR = ""
        if NavPosition == "top-right":  
            NavTop = "top: 5px;"
            NavRight = "right: 2px;"            
            NavRightR = "right: 16px;"
        if NavPosition == "top-left": 
            NavTop = "top: 1px;"
            NavLeft = "left: 14px;"
            NavLeftR = "left: 1px;"
        if NavPosition == "bottom-left": 
            NavBottom = "bottom: 1px;"
            NavLeft = "left: 14px;"
            NavLeftR = "left: 1px;"
        if NavPosition == "bottom-right":
            NavBottom = "bottom: 5px;"
            NavRight = "right: 5px;"
            NavRightR = "right: 18px;"
        
        css = css + u"""
.nav {
    cursor:pointer;  
    position: absolute;
    width: 11px;
    height: 16px;
    %s
    %s
    %s
    %s
}""" % (
        NavTop,
        NavBottom,
        NavLeft,
        NavRight
               )  
        css = css + u"""
.nav a, .nav a:hover, .nav a:link, .nav a:visited, .nav a:active {    
    text-decoration: none;    
    font-family: Arial, "Helvetica CY", "Nimbus Sans L", sans-serif;
    display: block;
    height: 16px; 
    width: 12px;    
}"""
        
        css = css + u"""
.navr {  
    cursor:pointer;  
    position: absolute;
    width: 11px;
    height: 16px; 
    %s
    %s
    %s
    %s
}""" % (
        NavTop,
        NavBottom,
        NavLeftR,
        NavRightR
           )
        css = css + u"""
.navr a, .nav a:hover, .navr a:link, .navr a:visited, .navr a:active {    
    text-decoration: none;
    font-family: Arial, "Helvetica CY", "Nimbus Sans L", sans-serif;
    display: block;
    height: 16px; 
    width: 12px;    
}"""
        if opt['Nav']["logoColor"] == "color":
            logo = "colorLogo.gif');"
        if opt['Nav']["logoColor"] == "blue":
            logo = "blueLogo.gif');"
        if opt['Nav']["logoColor"] == "black":
            logo = "blackLogo.gif');"
        if opt['Nav']["logoColor"] == "white":
            logo = "whiteLogo.gif');"
        
        try:
            mainwidth = int(re.findall('(\d+)', opt['Main']['width'])[0])
        except (IndexError):
            mainwidth = 200  
      
        if mainwidth < 200:           
            path = "background-image: url('http://cdnt.yottos.com/getmyad/logos/yot/"            
            logoW = "45"
        else:            
            path = "background-image: url('http://cdnt.yottos.com/getmyad/logos/"            
            logoW = "100"
            
        if NavLogoPosition == "top-right":  
            adInfo = "top: 3px;\nright: 1px;"
                                   
        if NavLogoPosition == "top-left": 
            adInfo = "top: 3px;\nleft: 1px;"  
                     
        if NavLogoPosition == "bottom-left": 
            adInfo = "bottom: 5px;\nleft: 0px;"
                       
        if NavLogoPosition == "bottom-right":
            adInfo = "bottom: 0px;\nright: 1px;"
            
        if opt['Nav'].get('logoHide'):
            adInfo += "\ndisplay: none;\n"
           
        css = css + """
#adInfo {
    position: absolute;
    %s
    background-repeat: no-repeat;
    overflow:hidden;
    %s
    height: 10px;
    width: %spx;
}    
        """ % (adInfo, path + logo, logoW)
        
        try:
            if NavBackgroundColor == 'red':
                NavBackgroundColor = 'FF0000'
            if len(NavBackgroundColor) < 1:
                NavBackgroundColor = '000000'
            if len(NavColor) >= 6:                
                xclr = {'r':int(NavColor[0:2], 16), 'g':int(NavColor[2:4], 16), 'b':int(NavColor[4:6], 16)}
            else: 
                xclr = {'r':int(NavColor[0:1], 16), 'g':int(NavColor[1:2], 16), 'b':int(NavColor[2:3], 16)}
            if len(NavBackgroundColor) >= 6:                
                yclr = {'r':int(NavBackgroundColor[0:2], 16), 'g':int(NavBackgroundColor[2:4], 16), 'b':int(NavBackgroundColor[4:6], 16)}
            else:
                yclr = {'r':int(NavBackgroundColor[0:1], 16), 'g':int(NavBackgroundColor[1:2], 16), 'b':int(NavBackgroundColor[2:3], 16)}

            cr = 1.5
            cg = 1.5
            cb = 1.5
            

            r = int((xclr['r'] + yclr['r']) / cr)
            g = int((xclr['g'] + yclr['g']) / cg)
            b = int((xclr['b'] + yclr['b']) / cb)
            if r > 255:                
                r = int((xclr['r'] + yclr['r']) / 2.2)
            if g > 255:
                g = int((xclr['g'] + yclr['g']) / 2.2)
            if b > 255:
                b = int((xclr['b'] + yclr['b']) / 2.2)
            hoverColor = rgb(r, g, b)
                                                           
        except Exception, ex:
            print ex                 
            return False

        css = css + """
#adInfo a {
width:100%;
height:100%;
display: block;

}"""
        css = css + """
.c {position: absolute; overflow-x: hidden; overflow-y: hidden; width: 1px; height: 1px;background-color:#%s;}
.c1 {position: absolute; overflow-x: hidden; overflow-y: hidden; width: 1px; height: 1px;background-color:#%s;}
.c2 {position: absolute; overflow-x: hidden; overflow-y: hidden; width: 1px; height: 1px;background-color:#%s;}
.b {position: absolute; overflow-x: hidden; overflow-y: hidden; width: 1px; height: 1px;background-color:#%s;}
.b1 {position: absolute; overflow-x: hidden; overflow-y: hidden; width: 1px; height: 1px;background-color:#%s;}
.b2 {position: absolute; overflow-x: hidden; overflow-y: hidden; width: 1px; height: 1px;background-color:#%s;}

</style>
         """ % (
              NavColor,
              NavBackgroundColor,
              hoverColor,
              NavColor,
              NavBackgroundColor,
              hoverColor
              )
         
    except Exception, ex:
        print "Error: %s" % (ex)
        return False   
    return css

def adoptions_to_css(opt, css):
    """
        валидация выгрузки из параметров в ксс
        upd: передал попроще, но нужно сделать как раньше, только учитывать, что не все параметры передаются пользователей, т.е. нужно подпрвить admaker
    """
    return adv_to_css(opt)
    try: 
        s_path = "background-image: url('http://cdnt.yottos.com/getmyad/logos/yot/"
        f_path = "background-image: url('http://cdnt.yottos.com/getmyad/logos/"
        if opt['Main']['width'] < 200:
            if css.find(s_path) < 1:
                if css.find(f_path) > 0:
                    css.replace(f_path, s_path)
        res = {"status":'ok', "css":css}
        
        html_re = re.compile(r"<.*?<.*?>")
        s_re = re.compile(r"<")
        size_re = re.compile(r"[0-9]{3,}?px")
        cl_re = re.compile(r"color")
        color_re = re.compile(r"/^#?([a-f0-9]{6}|[a-f0-9]{3})$/", re.IGNORECASE)
        for el in opt:
            for x in opt[el]:
                if re.match(html_re, str(opt[el][x])):
                    log.info(str(opt[el][x]))
                    res['status'] = 'fail'
                    res['css'] = str(res['css']) + str(opt[el][x]) + "\n" 
                if re.match(s_re, str(opt[el][x])):
                    log.info(str(opt[el][x]))
                    res['status'] = 'fail'
                    res['css'] = str(res['css']) + str(opt[el][x]) + "\n"
                if x == "top" | x == "left" | x == "width" | x == "height":
                    if not re.match(size_re, str(opt[el][x])):
                        log.info(str(opt[el][x]))
                        res['status'] = 'fail'
                        res['css'] = str(res['css']) + str(opt[el][x]) + "\n"
                if re.match(cl_re, str(x)):
                    if not re.match(color_re, str(opt[el][x])):
                        log.info(str(opt[el][x]))
                        res['status'] = 'fail'
                        res['css'] = str(res['css']) + str(opt[el][x]) + "\n"                    
    except Exception, ex:
        res['status'] = 'fail'
        log.info(str(ex))
        res['css'] = ex        
    return res




class AdvertiseController(BaseController):


    def __before__(self, action, **params):
        user = session.get('user')
        if user:
            request.environ['CURRENT_USER'] = user
            request.environ['IS_MANAGER'] = session.get('isManager', False)

    
    def maker(self, id):
        if not id:
            return u"Не указан id выгрузки!"
        
        adv = app_globals.db.informer.find_one({'guid': id})
        if not adv:
            return u"Не найдена указанная выгрузка!"
        
        t = adv.get('admaker')
        c.admaker = h.JSON(t) if t else None
        c.adv_id = id
        return render('/admaker.mako.html')
    
    
    def save(self):
        try:
            user = session.get('user')
            if not user:
                return h.JSON({'error': True, 'message': u'Не выполнен вход'})
            id = request.params.get('adv_id')
            object = json.loads(request.body)
            informer = model.Informer()
            informer.guid = id
            informer.user_login = user
            informer.admaker = object.get('options')
            informer.css = str(adv_to_css(object.get('options')))
            informer.title = object.get('title')
            informer.domain = object.get('domain')
            informer.non_relevant = object.get('nonRelevant')

            informer.save()
            return h.JSON({'error': False, 'id': informer.guid})      
        except Exception, ex:
            log.debug("Error in advertise.save(): " + str(ex))            
            return h.JSON({'error': True, 'id': informer.guid})            
                   
        
    def showList(self):
        user = session.get('user')
        if not user:
            return "Login!"
        advertises = app_globals.db.informer.find().sort('user')
        data = [{'title': x['title'],
                 'guid': x['guid'],
                 'user': x['user']
                 } for x in advertises ]
        return render('/advertiseList.mako.html', extra_vars={'data': data})
            
    def days(self):
        """Возвращает разбитые по дням клики для каждой выгрузки текущего пользователя (для графиков).
        Формат: [{adv: {
                    guid: '...',
                    title: '...'
                  },
                  data: [[datestamp, clicks], [datestamp, clicks], ...],
            ...]
        """
        user = session.get('user')
        if not user:
            return ""

        result = []
        for adv in model.Account(user).informers():
            data = [(int(time.mktime(x['date'].timetuple()) * 1000), x['unique'])
                    for x in statGroupedByDate(adv.guid)]
            data.sort(key=lambda x:x[0])
            result.append({'adv': {'guid': adv.guid,
                                   'title': adv.title,
                                   'domain': adv.domain},
                           'data': data})
        return h.JSON(result)
    
    
    def domainsAdvertises(self):
        """ Возвращает выгрузки относящиеся к домену"""
        user = session.get('user')
        domain = request.params.get('domain')
        advertises = self._domainsAdvertises(domain)
        
        return h.jgridDataWrapper(advertises)
    
    
    def _domainsAdvertises(self, domain):
        """ Возвращает выгрузки относящиеся к домену"""
        if (domain != ''):
            advertises = [ (x['title'], x['guid'])
                          for x in app_globals.db.informer.find({'user': session.get('user'), 'domain': domain})]
        else:
            advertises = [ (x['title'], x['guid'])
                          for x in app_globals.db.informer.find({'user': session.get('user'), 'domain': {'$exists': False} })]    
        return advertises
    

    def daysSummary(self):
        """Возвращает данные для таблицы суммарной статистики по дням """
        user = session.get('user')
        dateStart = dateFromStr(request.params.get('dateStart', None))
        dateEnd = dateFromStr(request.params.get('dateEnd', None))
        adv = request.params.get('adv')
        if user:
            from math import ceil
            try:
                page = int(request.params.get('page'))
                rows = int(request.params.get('rows'))
            except:
                page = 1
                rows = 30
            if not adv:
                advertises = [adv.guid for adv in model.Account(user).informers()]
            else:
                advertises = [adv]
            data = statGroupedByDate(advertises, dateStart, dateEnd)
            data.sort(key=lambda x:x['date'])
            data.reverse()
            totalPages = int(ceil(float(len(data)) / rows))
            data = data[(page - 1) * rows : page * rows]
            data = [{'id': index,
                     'cell': (
                              "<b>%s</b>" % x['date'].strftime("%d.%m.%Y"),
                              x['impressions'],
                              x['clicks'],
                              x['unique'],
                              '%.3f%%' % (round(x['clicks'] * 100 / x['impressions'], 3) if x['impressions'] <> 0 else 0),
                              '%.3f%%' % (round(x['unique'] * 100 / x['impressions'], 3) if x['impressions'] <> 0 else 0),
                              '%.2f $' % (x['summ'] / x['unique']) if x['unique'] else 0,
                              '%.2f $' % x['summ']
                            )
                     }
                    for index, x in enumerate(data)]
            return json.dumps({'total': totalPages,
                               'page': page,
                               'records': len(data),
                               'rows': data
                               },
                               default=pymongo.json_util.default, ensure_ascii=False)
        else:
            return ""
        
    
    def allAdvertises(self):
        """ Суммарный отчёт по всем рекламным площадкам """
#        time.sleep(1)
        user = session.get('user')
        dateStart = dateFromStr(request.params.get('dateStart', None))
        dateEnd = dateFromStr(request.params.get('dateEnd', None))
        
        reportData = allAdvertiseScriptsSummary(user, dateStart, dateEnd)
        reportData.sort(cmp=lambda x, y: cmp(x['advTitle'], y['advTitle']), key=None, reverse=False)
        data = [{'id': r['adv'], 'cell': [r['advTitle'], r['impressions'], r['clicks'], r['unique'],
                                           '%.3f%%' % round(r['clicks'] * 100 / r['impressions'], 3) if r['impressions'] <> 0 else 0,
                                           '%.3f%%' % round(r['unique'] * 100 / r['impressions'], 3) if r['impressions'] <> 0 else 0,
                                           '%.2f $' % round(r['totalCost'] / r['unique'], 2) if r['unique'] <> 0 else 0,
                                           '%.2f $' % round(r['totalCost'], 2)
                                           ]
                                           }
                for index, r in enumerate(reportData)]
        totalImpressions = sum([r['impressions'] for r in reportData if 'impressions' in r])
        totalClicks = sum([r['clicks'] for r in reportData if 'clicks' in r])
        totalUnique = sum([r['unique'] for r in reportData if 'unique' in r])
        totalCost = sum([r['totalCost'] for r in reportData if 'totalCost' in r])
            
         
        return json.dumps({'total': len(data),
                           'page': 1,
                           'records': len(data),
                           'rows': data,
                           'userdata': {u"Title": u"ИТОГО",
                                        "Impressions":    totalImpressions,
                                        "RecordedClicks": totalClicks,
                                        "UniqueClicks":   totalUnique,
                                        "CTR":            '%.3f%%' % round(totalClicks * 100 / totalImpressions, 3) if totalImpressions <> 0 else 0,
                                        "CTR_Unique":     '%.3f%%' % round(totalUnique * 100 / totalImpressions, 3) if totalImpressions <> 0 else 0,
                                        "Summ":   '%.2f $' % totalCost,
                                       }
                           },
                           default=pymongo.json_util.default, ensure_ascii=False)


    def create(self):
        """Создание выгрузки"""
        user = request.environ.get('CURRENT_USER')
        if not user:
            redirect(url_for(controller='main', action='index'))
        c.patterns = self._patterns()
        c.advertise = None
        c.domains = model.Account(login=user).domains()
        return render("/create_adv.mako.html")
    
    
    def edit(self):
        """Редактирование выгрузки"""
        user = request.environ.get('CURRENT_USER')
        if not user:
            redirect(url_for(controller='main', action='index'))
        guid = request.params.get('ads_id')
        x = app_globals.db.informer.find_one({'guid': guid})
        if not x: return u"Информер не найден!"
        
        advertise = {'title': x['title'],
                     'guid': x['guid'],
                     'options': x['admaker'],
                     'domain': x.get('domain', ''),
                     'non_relevant': x.get('nonRelevant')
                    }
        from webhelpers.html.builder import escape as html_escape
        advertise['non_relevant']['userCode'] = \
            unicode(html_escape(advertise['non_relevant'].get('userCode', '')))

        c.patterns = self._patterns()
        c.advertise = advertise
        c.domains = model.Account(login=user).domains()
        return render("/create_adv.mako.html")


    def _patterns(self):
        """Возвращает образцы выгрузок"""
        return [{'title': x['title'],
                 'guid': x['guid'],
                 'options': x['admaker'],
                 'orient': x.get('orient'),
                 'popular': x.get('popular')}
                 for x in app_globals.db.informer.find({'user': 'patterns'}).sort('title')] 
    

