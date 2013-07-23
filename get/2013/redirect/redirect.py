#!/usr/bin/python
# This Python file uses the following encoding: utf-8
import os, sys
project_dir = os.path.dirname( os.path.realpath( __file__ ) )
sys.path.append(project_dir)
os.environ['PYTHON_EGG_CACHE'] = '/usr/lib/python2.6/dist-packages'
import base64
import datetime
import unittest
import urlparse
import tasks
import sys
import pymongo
import urllib
import random
import re
from pprint import pprint

sys.stdout = sys.stderr

MONGO_HOST = '213.186.121.76:27018,213.186.121.199:27018,yottos.com'


def redirect(environ, start_response):

    def _redirect_to(url):
        ''' Перенаправление на ``url`` '''
        response_headers = [('Location',   url),
                            ('Connection', 'close')]
        start_response("301 Moved Permanently", response_headers)
        return ""

    # Получаем словарь параметров
    try:
        elapsed_start_time = datetime.datetime.now()
        # Отделяем дополнительные GET-параметры от основных,
        # закодированных в base64
        status = environ['QUERY_STRING'].partition('&')[0]
        if status == 'status':
            start_response('200 OK', [('Content-type', 'text/plain')])
            return ""
        base64_encoded_params = environ['QUERY_STRING'].partition('&')[0]
        referer = environ.get('HTTP_REFERER', 'None')
        user_agent = environ.get('HTTP_USER_AGENT', 'None')
        param_lines = base64.urlsafe_b64decode(base64_encoded_params) \
                      .splitlines()
        params = dict([(x.partition('=')[0], x.partition('=')[2])
                       for x in param_lines])
        url = params.get('url')
        cookie = environ.get('HTTP_COOKIE', 'N=N')
        cookie = dict( (n,v) for n,v in (b.split('=') for b in cookie.split(';') ) ).get('yottos_unique_id', None)

        # Проверяем действительность токена
        ip=environ['REMOTE_ADDR']
        offer_id=params.get('id')
        server=params.get('server')
        #print 'Worker database server:', server
        token=params.get('token')
        valid = False
        country = 'NOT FOUND'
        city = 'NOT FOUND'
        social = False
        title = 'Non Title'
        campaignTitle = 'Non Title'
        type = 'teaser'
        project = 'adload'
        isOnClick = True
        branch = 'L0'
        conformity = ''
        matching = ''
        mongo_log = pymongo.Connection(host=server, tz_aware=False).getmyad
        view_seconds = 0
        if cookie != None:
            for x in mongo_log.log.impressions.find({'ip': ip, 'cookie' : cookie}):
                if x['token'] == token and x['id'] == offer_id:
                    #print 'Cookies Valid - %s' % cookie
                    valid = True
                    title = x.get('title', 'Non Title')
                    campaignTitle = x.get('campaignTitle', 'Non Title')
                    social = x.get('social', False)
                    country = x.get('country', 'NOT FOUND')
                    city = x.get('region', 'NOT FOUND')
                    type = x.get('type', 'teaser')
                    project = x.get('project', 'adload')
                    isOnClick = x.get('isOnClick', True)
                    branch = x.get('branch', '')
                    conformity = x.get('conformity', '')
                    matching = x.get('matching', '')
                    redirect_datetime = datetime.datetime.utcnow()
                    view_datetime = x.get('dt', redirect_datetime)
                    if redirect_datetime > view_datetime:
                        view_seconds = (redirect_datetime - view_datetime).seconds
                    break
        else:
            for x in mongo_log.log.impressions.find({'token': token}):
                if x['ip'] == ip and x['id'] == offer_id:
                    #print 'Cookies Invalid - %s' % cookie
                    valid = True
                    title = x.get('title', 'Non Title')
                    campaignTitle = x.get('campaignTitle', 'Non Title')
                    social = x.get('social', False)
                    country = x.get('country', 'NOT FOUND')
                    city = x.get('region', 'NOT FOUND')
                    type = x.get('type', 'teaser')
                    project = x.get('project', 'adload')
                    isOnClick = x.get('isOnClick', True)
                    branch = x.get('branch', '')
                    conformity = x.get('conformity', '')
                    matching = x.get('matching', '')
                    redirect_datetime = datetime.datetime.utcnow()
                    view_datetime = x.get('dt', redirect_datetime)
                    if redirect_datetime > view_datetime:
                        view_seconds = (redirect_datetime - view_datetime).seconds
                    #print view_seconds
                    break

        # Выделяем домен партнёра и добавляем его в целевой url
        partner_domain = urlparse.urlsplit(params.get('loc')).netloc
        if not partner_domain:
            partner_domain = _get_informer_domain(params.get('inf'))
        partner_domain = partner_domain.replace('.', '_')
        offer_title = 'yottos-' + title.encode('utf-8').replace(' ', '_').replace('.', '_').replace(',', '_').replace(';', '_').replace('!', '_').replace('?', '_')
        offer_title = urllib.quote(offer_title)
        offer_campaign_title = 'yottos-' + campaignTitle.encode('utf-8').replace(' ', '_').replace('.', '_').replace(',', '_').replace(';', '_').replace('!', '_').replace('?', '_')
        offer_campaign_title = urllib.quote(offer_campaign_title)
        offer_matching = matching.encode('utf-8').replace(' ', '_').replace('.', '_').replace(',', '_').replace(';', '_').replace('!', '_').replace('?', '_')
        offer_matching = urllib.quote(offer_matching)
        url = _add_dynamic_param(url, partner_domain, offer_campaign_title, offer_title, offer_matching)
        if _need_yottos_partner_marker(offer_id=params.get('id')):
            url = _add_utm_param(url, type, partner_domain, offer_campaign_title, offer_title, offer_matching)
        try:
            tasks.process_click.delay(url=url,
                                      ip=ip,
                                      click_datetime=datetime.datetime.now(),
                                      offer_id=offer_id,
                                      informer_id=params.get('inf'),
                                      token=token,
                                      server=server,
                                      valid=valid,
                                      social=social,
                                      type=type,
                                      project=project,
                                      isOnClick=isOnClick,
                                      branch=branch,
                                      conformity=conformity,
                                      matching=matching,
                                      title=title,
                                      country=country,
                                      city=city,
                                      referer=referer,
                                      user_agent=user_agent,
                                      cookie=cookie,
                                      view_seconds=view_seconds)
        except Exception as ex:
            tasks.process_click(url=url,
                                ip=ip,
                                click_datetime=datetime.datetime.now(),
                                offer_id=offer_id,
                                informer_id=params.get('inf'),
                                token=token,
                                server=server,
                                valid=valid,
                                social=social,
                                type=type,
                                project=project,
                                isOnClick=isOnClick,
                                branch=branch,
                                conformity=conformity,
                                matching=matching,
                                title=title,
                                country=country,
                                city=city,
                                referer=referer,
                                user_agent=user_agent,
                                cookie=cookie,
                                view_seconds=view_seconds)
            print ex
    except Exception as e:
        print e
        return _redirect_to('http://yottos.com')
    #print 'Redirect complit to %s ' % (datetime.datetime.now() - elapsed_start_time).microseconds
    return _redirect_to(url or 'http://yottos.com')


def _add_url_param(url, param, value):
    ''' Добавляет параметр ``param`` со значением ``value`` в ``url`` если такого параметра не сушествует'''
    url_parts = list(urlparse.urlparse(url))
    query = dict(urlparse.parse_qsl(url_parts[4]))
    if not query.has_key(param):
        query.update({param:value})
    url_parts[4] = urllib.urlencode(query)
    return urlparse.urlunparse(url_parts)

def _url_param_safe_check(param):
    """
    Костыль для вот этого рекламодателя bonprix, потому что мы перед ним либизим :))
    """
    pattern = '(&{0,}[^&=]{0,}={1}[^&=]{0,})(\?)'
    if (re.search(pattern, param) is None):
        safe = True
    else:
        safe = False
    return safe

def _add_dynamic_param(url, sourse, campaign, name, matching):
    url_parts = list(urlparse.urlparse(url))

    params = dict(urlparse.parse_qsl(url_parts[3]))
    if ((len(params) > 0) and _url_param_safe_check(url_parts[3])):
        for key, value in params.items():
            if value == '{source}':
                params[key] = sourse
            elif value == '{campaign}':
                params[key] = campaign
            elif value == '{name}':
                params[key] = name
            elif value == '{matching}':
                params[key] = matching
            elif value == '{rand}':
                params[key] = random.randint(0,1000000)
            else:
                pass
        url_parts[3] = urllib.urlencode(params)

    query = dict(urlparse.parse_qsl(url_parts[4]))
    if ((len(query) > 0) and _url_param_safe_check(url_parts[4])):
        for key, value in query.items():
            if value == '{source}':
                query[key] = sourse
            elif value == '{campaign}':
                query[key] = campaign
            elif value == '{name}':
                query[key] = name
            else:
                pass
        url_parts[4] = urllib.urlencode(query)

    return urlparse.urlunparse(url_parts)

def _add_utm_param(url, type, sourse, campaign, name, matching):
    url_parts = list(urlparse.urlparse(url))
    if not _url_param_safe_check(url_parts[4]):
        return urlparse.urlunparse(url_parts)
    query = dict(urlparse.parse_qsl(url_parts[4]))

    if (type == 'banner'):
        utm_medium = 'cpm_yottos'
    else:
        utm_medium = 'cpc_yottos'
    utm_source =  str(sourse or 'other')
    utm_campaign = str(campaign)
    utm_content = str(name)
    if query.has_key('utm_source'):
        utm_term = str(sourse or 'other')
    else:
        utm_term = str(matching)

    if not query.has_key('utm_medium'):
        query.update({'utm_medium':utm_medium})
    if not query.has_key('utm_source'):
        query.update({'utm_source':utm_source})
    if not query.has_key('utm_campaign'):
        query.update({'utm_campaign':utm_campaign})
    if not query.has_key('utm_content'):
        query.update({'utm_content':utm_content})
    if not query.has_key('utm_term'):
        query.update({'utm_term':utm_term})
    url_parts[4] = urllib.urlencode(query)
    return urlparse.urlunparse(url_parts)

def _get_informer_domain(informer_id):
    ''' Возвращает домен, к которому относится информер ``informer_id`` '''
    try:
        db = pymongo.Connection(MONGO_HOST).getmyad_db
        return str(db.informer.find_one({'guid': informer_id})['domain'])
    except (AttributeError, KeyError):
        return informer_id
    except pymongo.errors.AutoReconnect:
        return informer_id

def _need_yottos_partner_marker(offer_id):
    ''' Возвращает True, если к ссылке перехода на рекламное предложение
        ``offer_id`` необходимо добавить маркер yottos_partner=... '''
    try:
        db = pymongo.Connection(MONGO_HOST).getmyad_db
        campaign_id = db.offer.find_one({'guid': offer_id},
                                        ['campaignId'])['campaignId']
        need_marker = db.campaign.find_one({'guid': campaign_id},
                                           ['yottosPartnerMarker']) \
                                 .get('yottosPartnerMarker', True)
        return need_marker
    except (AttributeError, KeyError):
        return True
    except pymongo.errors.AutoReconnect:
        return True

def _need_yottos_attractor_marker(offer_id):
    ''' Возвращает True, если к ссылке перехода на рекламное предложение
        ``offer_id`` необходимо добавить маркер ... '''
    try:
        db = pymongo.Connection(MONGO_HOST).getmyad_db
        campaign_id = db.offer.find_one({'guid': offer_id},
                                        ['campaignId'])['campaignId']
        need_marker = db.campaign.find_one({'guid': campaign_id},
                                           ['yottosAttractorMarker']) \
                                 .get('yottosAttractorMarker', True)
        return need_marker
    except (AttributeError, KeyError):
        return True
    except pymongo.errors.AutoReconnect:
        return True

class TestAddParamToUrl(unittest.TestCase):

    def test_url_has_no_params(self):
        self.assertEqual(_add_url_param(
                         'http://ex.com/index.php', 'key', 'value'),
                         'http://ex.com/index.php?key=value')

    def test_url_has_one_param(self):
        self.assertEqual(_add_url_param(
                         'http://ex.com/index.php?p=1', 'key', 'value'),
                         'http://ex.com/index.php?p=1&key=value')

    def test_url_with_hash(self):
        self.assertEqual(_add_url_param(
                         'http://ex.com/index.php?p=1#hash', 'key', 'value'),
                         'http://ex.com/index.php?p=1&key=value#hash')

    def test_national_domain(self):
        self.assertEqual(_add_url_param(
                         'http://тест.com/index.php?p=1#hash', 'key', 'value'),
                         'http://тест.com/index.php?p=1&key=value#hash')


if __name__ == '__main__':
    unittest.main()

application = redirect
