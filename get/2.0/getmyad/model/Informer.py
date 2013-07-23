# This Python file uses the following encoding: utf-8
from ftplib import FTP
from getmyad.config.social_ads import social_ads
from getmyad.lib.helpers import progressBar
from getmyad.lib.admaker_validator import validate_admaker
from getmyad.lib.template_convertor import js2mako
from getmyad.model import mq
from pylons import config, app_globals
import mako.template
from uuid import uuid1
import StringIO
import datetime
import logging
import re


class Informer:
    """ Рекламный информер (он же рекламный скрипт, рекламная выгрузка) """

    def __init__(self):
        self.guid = None
        self.title = None
        self.admaker = None
        self.css = None
        self.user_login = None
        self.non_relevant = None
        self.domain = None
        self.height = None
        self.width = None
        self.db = app_globals.db

    def save(self):
        """ Сохраняет информер, при необходимости создаёт """
        update = {}
        if self.guid:
            update['guid'] = self.guid
        if self.title:
            update['title'] = self.title
        if self.admaker:
            update['admaker'] = self.admaker
        if self.css:
            update['css'] = self.css
        else:
            update['css'] = self.admaker_options_to_css(self.admaker)
        if self.domain:
            update['domain'] = self.domain
        if self.height:
            update['height'] = self.height
        if self.width:
            update['width'] = self.width
        if isinstance(self.non_relevant, dict) \
                        and 'action' in self.non_relevant \
                        and 'userCode' in self.non_relevant:
            update['nonRelevant'] = {'action': self.non_relevant['action'],
                                     'userCode': self.non_relevant['userCode']}
        update['lastModified'] = datetime.datetime.now()

        if not self.guid:
            # Создание нового информера
            if not self.user_login:
                raise ValueError('User login must be specified when creating '
                                 'informer!')
            self.guid = str(uuid1()).lower()
            update['user'] = self.user_login
        else:
            if self.user_login:
                pass      # TODO: Выдавать предупреждение, что для
                          # уже созданных информеров нельзя менять пользователя

        self.db.informer.update({'guid': self.guid},
                                       {'$set': update},
                                       upsert=True,
                                       safe=True)
        InformerFtpUploader(self.guid).upload()
        mq.MQ().informer_update(self.guid)

    def load(self, id):
        raise NotImplementedError

    @staticmethod
    def load_from_mongo_record(mongo_record):
        """ Загружает информер из записи MongoDB """
        informer = Informer()
        informer.guid = mongo_record['guid']
        informer.title = mongo_record['title']
        informer.user_login = mongo_record["user"]
        informer.admaker = mongo_record.get('admaker')
        informer.css = mongo_record.get('css')
        informer.domain = mongo_record.get('domain')
        if 'nonRelevant' in mongo_record:
            informer.non_relevant = {}
            informer.non_relevant['action'] = \
                mongo_record['nonRelevant'].get('action', 'social')
            informer.non_relevant['userCode'] = \
                mongo_record['nonRelevant'].get('userCode', '')
        return informer

    def admaker_options_to_css(self, options):
        """ Создаёт строку CSS из параметров Admaker """

        def parseInt(value):
            ''' Пытается выдрать int из строки.
                
                Например, для "128px" вернёт 128. '''
            try:
                return re.findall("\\d+", value)[0]
            except IndexError:
                return 0

        options = validate_admaker(options)
        template_name = '/advertise_style_template.mako.html'
        src = app_globals.mako_lookup.get_template(template_name)\
                .source.replace('<%text>', '').replace('</%text>', '')
        template = mako.template.Template(
            text=js2mako(src), 
            format_exceptions=True)
        return template.render_unicode(parseInt=parseInt, **options)
#        return minify_css( template.render_unicode(parseInt=h.parseInt, **opt) )


class InformerFtpUploader:
    """ Заливает необходимое для работы информера файлы на сервер раздачи
        статики:

        1. Javascript-загрузчик информера.
        2. Статическую заглушку с социальной рекламой на случай отказа GetMyAd.
    """

    def __init__(self, informer_id):
        self.informer_id = informer_id
        self.db = app_globals.db

    def upload(self):
        """ Заливает через FTP загрузчик и заглушку информера """
        self.upload_loader()
        self.upload_reserve()

    def upload_loader(self):
        ' Заливает загрузчик информера '
        if config.get('informer_loader_ftp'):
            try:
                ftp = FTP(host=config.get('informer_loader_ftp'),
                          user=config.get('informer_loader_ftp_user'),
                          passwd=config.get('informer_loader_ftp_password'))
                ftp.cwd(config.get('informer_loader_ftp_path'))
                loader = StringIO.StringIO()
                loader.write(self._generate_informer_loader())
                loader.seek(0)
                # TODO: Приведение к UPPER-CASE нужно будет убрать, когда
                #       на сервере будет реализована case-insensitive раздача
                #       статических файлов (задача #58).
                ftp.storlines('STOR %s.js' % self.informer_id.lower(), loader)
                ftp.storlines('STOR %s.js' % self.informer_id.upper(), loader)
                ftp.quit()
                loader.close()
            except Exception, ex:
                logging.error(ex)
        else:
            logging.warning('informer_loader_ftp settings not set! '
                            'Check .ini file.')

    def upload_reserve(self):
        ' Заливает заглушку для информера '
        if config.get('reserve_ftp'):
            try:
                ftp = FTP(config.get('reserve_ftp'))
                ftp.login(config.get('reserve_ftp_user'),
                          config.get('reserve_ftp_password'))
                ftp.cwd(config.get('reserve_ftp_path'))
                data = StringIO.StringIO()
                data.write(self._generate_social_ads().encode('utf-8'))
                data.seek(0)
                ftp.storlines('STOR emergency-%s.html' % self.informer_id,
                              data)
                ftp.quit()
                data.close()
            except Exception, ex:
                logging.error(ex)
        else:
            logging.warning('reserve_ftp settings not set! Check .ini file.')

    def uploadAll(self):
        """ Загружает на FTP скрипты для всех информеров """
        advertises = self.db.informer.find({}, {'guid': 1})
        prog = progressBar(0, advertises.count())
        i = 0
        for adv in advertises:
            i += 1
            prog.updateAmount(i)
#            print "Saving informer %s... \t\t\t %s" % (adv['guid'], prog)
            InformerFtpUploader(adv['guid']).upload()

    def _generate_informer_loader(self):
        ''' Возвращает код javascript-загрузчика информера '''
        adv = self.db.informer.find_one({'guid': self.informer_id})
        if not adv:
            return False
        try:
            guid = adv['guid']
            width = int(re.match('[0-9]+',
                        adv['admaker']['Main']['width']).group(0))
            height = int(re.match('[0-9]+',
                         adv['admaker']['Main']['height']).group(0))
        except:
            raise Exception("Incorrect size dimensions for informer %s" %
                             self.informer_id)
        try:
            border = int(re.match('[0-9]+',
                         adv['admaker']['Main']['borderWidth']).group(0))
        except:
            border = 1
        partner = adv.get('domain', 'other').replace('.', '_').replace('/', '')
        width += border * 2
        height += border * 2
        return (""";function windowWidth(){var a=document.documentElement;return self.innerWidth||a&&a.clientWidth||document.body.clientWidth}"""
                """;function windowHeight(){var a=document.documentElement;return self.innerHeight||a&&a.clientHeight||document.body.clientHeight}"""
                """;document.write("<iframe src='http://%s.rg.yottos.com/adshow.fcgi?scr=%s&location=" + """
                """encodeURIComponent(window.location.href) + "&referrer=" + encodeURIComponent(document.referrer) + """
                """ "&w=" + windowWidth() + "&h=" + windowHeight() + """
                """ "&rand=" + Math.floor(Math.random() * 1000000) + "' width='%s' height='%s'  frameborder='0' scrolling='no'></iframe>");"""
                ) % (partner, guid, width, height)

    def _generate_social_ads(self):
        ''' Возвращает HTML-код заглушки с социальной рекламой,
            которая будет показана при падении сервиса
        '''
        inf = self.db.informer.find_one({'guid': self.informer_id})
        if not inf:
            return

        try:
            items_count = int(inf['admaker']['Main']['itemsNumber'])
        except:
            items_count = 0

        offers = ''
        for i in xrange(0, items_count):
            adv = social_ads[i % len(social_ads)]

            offers += ('''<div class="advBlock"><a class="advHeader" href="%(url)s" target="_blank">''' +
                       '''%(title)s</a><a class="advDescription" href="%(url)s" target="_blank">''' +
                       '''%(description)s</a><a class="advCost" href="%(url)s" target="_blank"></a>''' +
                       '''<a href="%(url)s" target="_blank"><img class="advImage" src="%(img)s" alt="%(title)s"/></a></div>'''
                       ) % {'url': adv['url'], 'title': adv['title'], 'description': adv['description'], 'img': adv['image']}
        return '''
<html><head><META http-equiv="Content-Type" content="text/html; charset=utf-8"><meta name="robots" content="nofollow" /><style type="text/css">html, body { padding: 0; margin: 0; border: 0; }</style><!--[if lte IE 6]><script type="text/javascript" src="http://cdn.yottos.com/getmyad/supersleight-min.js"></script><![endif]-->
%(css)s
</head>
<body>
<div id='mainContainer'><div id="ads" style="position: absolute; left:0; top: 0">
%(offers)s
</div><div id='adInfo'><a href="http://yottos.com.ua" target="_blank"></a></div>
</body>
</html>''' % {'css': inf.get('css'), 'offers': offers}





def minify_css(css):
    # remove comments - this will break a lot of hacks :-P
    css = re.sub( r'\s*/\*\s*\*/', "$$HACK1$$", css ) # preserve IE<6 comment hack
    css = re.sub( r'/\*[\s\S]*?\*/', "", css )
    css = css.replace( "$$HACK1$$", '/**/' ) # preserve IE<6 comment hack
    
    # url() doesn't need quotes
    css = re.sub( r'url\((["\'])([^)]*)\1\)', r'url(\2)', css )
    
    # spaces may be safely collapsed as generated content will collapse them anyway
    css = re.sub( r'\s+', ' ', css )
    
    # shorten collapsable colors: #aabbcc to #abc
    css = re.sub( r'#([0-9a-f])\1([0-9a-f])\2([0-9a-f])\3(\s|;)', r'#\1\2\3\4', css )
    
    # fragment values can loose zeros
    css = re.sub( r':\s*0(\.\d+([cm]m|e[mx]|in|p[ctx]))\s*;', r':\1;', css )
    
    result = []
    for rule in re.findall( r'([^{]+){([^}]*)}', css ):
    
        # we don't need spaces around operators
        selectors = [re.sub( r'(?<=[\[\(>+=])\s+|\s+(?=[=~^$*|>+\]\)])', r'', selector.strip() ) for selector in rule[0].split( ',' )]
    
        # order is important, but we still want to discard repetitions
        properties = {}
        porder = []
        for prop in re.findall( '(.*?):(.*?)(;|$)', rule[1] ):
            key = prop[0].strip().lower()
            if key not in porder: porder.append( key )
            properties[ key ] = prop[1].strip()
    
        # output rule if it contains any declarations
        if properties:
            result.append( "%s{%s}" % ( ','.join( selectors ), ''.join(['%s:%s;' % (key, properties[key]) for key in porder])[:-1] ))
    return "\n".join(result)
