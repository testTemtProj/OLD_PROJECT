# encoding: utf-8
from getmyad.lib.base import BaseController, render
from getmyad.tasks import tasks
from pylons import request, response, session, tmpl_context as c, url
from pylons.controllers.util import abort, redirect
import base64
import datetime
import logging
import urlparse
import pymongo


MONGO_HOST = '213.186.121.201:27018,213.186.121.84:27018,yottos.com'

log = logging.getLogger(__name__)


class AdshowController(BaseController):

    def redirect(self):
        ''' Редирект на рекламное предложение.

        Использует следующие GET параметры:

            ``url``      url назначения (куда редиректим) в base64.
            ``inf``      guid информера, с которого производим редирект
            ``id``       guid рекламного предложения
            ``token``    токен (секретное значения для обеспечения
                         уникальности ссылки)
        '''
        # TODO: Обновить документацию

        # Получаем словарь параметров
        try:
            # Отделяем дополнительные GET-параметры от основных,
            # закодированных в base64
            base64_encoded_params = request.query_string.partition('&')[0]
            param_lines = base64.urlsafe_b64decode(base64_encoded_params) \
                                .splitlines()
            params = dict([(x.partition('=')[0], x.partition('=')[2])
                           for x in param_lines])
            url = params.get('url')

            # Выделяем домен партнёра и добавляем его в целевой url
            if self._need_yottos_partner_marker(offer_id=params.get('id')):
                partner_domain = urlparse.urlsplit(params.get('loc')).netloc
                if not partner_domain:
                    partner_domain = self._get_informer_domain(params.get('inf'))
                url = self._add_url_param(url, 'yottos_partner',
                                          partner_domain or 'other')

        except Exception:
            return self._redirect_to('http://yottos.com')

        try:
            tasks.process_click.delay(url=url,
                                      ip=request.environ['REMOTE_ADDR'],
                                      click_datetime=datetime.datetime.now(),
                                      offer_id=params.get('id'),
                                      informer_id=params.get('inf'),
                                      token=params.get('token'),
                                      server=params.get('server'))
        except Exception as ex:
            tasks.process_click(url=url,
                                ip=request.environ['REMOTE_ADDR'],
                                click_datetime=datetime.datetime.now(),
                                offer_id=params.get('id'),
                                informer_id=params.get('inf'),
                                token=params.get('token'),
                                server=params.get('server'))

        return self._redirect_to(url or 'http://yottos.com')

    def _add_url_param(self, url, param, value):
        ''' Добавляет параметр ``param`` со значением ``value`` в ``url`` '''
        splitted = list(urlparse.urlparse(url))
        if splitted[4]:
            splitted[4] += '&%s=%s' % (param, value)
        else:
            splitted[4] = '%s=%s' % (param, value)
        return urlparse.urlunparse(splitted)

    def _get_informer_domain(self, informer_id):
        ''' Возвращает домен, к которому относится информер ``informer_id`` '''
        try:
            db = pymongo.Connection(MONGO_HOST).getmyad_db
            return str(db.informer.find_one({'guid': informer_id})['domain'])
        except (AttributeError, KeyError):
            return informer_id
        except pymongo.errors.AutoReconnect:
            return informer_id

    def _need_yottos_partner_marker(self, offer_id):
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

    def _redirect_to(self, url):
        ''' Перенаправление на ``url`` '''
        return redirect(url, 301)
