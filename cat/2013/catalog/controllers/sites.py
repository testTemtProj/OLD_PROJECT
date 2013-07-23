from pprint import pprint

import logging
import re 
import catalog.lib.helpers as h
from formencode import Schema, FancyValidator, validators, Invalid
from pylons import request, response, session, tmpl_context as c, url
from pylons.controllers.util import abort, redirect
from catalog.lib.base import BaseController, render
from catalog.model.SiteModel import SiteModel
from catalog.model.item.SiteItem import SiteItem
from catalog.model.CategoryModel import CategoryModel
from catalog.lib.base import *
from pylons import session
from pylons.i18n import get_lang, set_lang
from gettext import gettext as _

log = logging.getLogger(__name__)

class SitesController(BaseController):
    def index(self):
        c.sites = SiteModel.get_by_category(int(request.params['cat_id']))
        return render('/sites_index.html')

    def add(self):
        c.errors = {}
        c.form_data = {}
        if request.POST:
            field_validator = FieldValidator()
            lang_fields_validator = LangFieldsValidator()

            try:
                field_validator.to_python(dict(request.params))
                data = lang_fields_validator.to_python(dict(request.params))

            except Invalid, error:
                #pprint(error.value)
                c.form_data = error.value
                c.errors = error.error_dict if error.error_dict else {}
                return render ('/site/add.mako.html')

            else:
                data['checked'] = True
                data['avaible'] = True
                SitesController._save(data)
                return render('/site/thanks.mako.html')
                    

        return render ('/site/add.mako.html')

    @staticmethod
    def _save(site):
        site = dict(site)
        if site.has_key('save'):
            del site['save']
        SiteItem.save(SiteItem(site))
        


class FieldValidator(Schema):

    allow_extra_fields=True
    filter_extra_fields=True
    reference = validators.URL(add_http=False, check_exists=True, not_empty=True)
    owners_mail =  validators.Email(not_empty=True)
    category_id = validators.Int()
    
    name_ru = validators.String(min=10,max=100, not_empty=False)
    name_uk = validators.String(min=10,max=100, not_empty=False)
    name_en = validators.String(min=10,max=100, not_empty=False)
    description_ru = validators.String(min=10,max=1000, not_empty=False)
    description_uk = validators.String(min=10,max=1000, not_empty=False)
    description_en = validators.String(min=10,max=1000, not_empty=False)
    date_add = validators.DateValidator()

class LangFieldsValidator(FancyValidator):

    messages = {
            'fields_empty' : _('Please fill in the fields at least for one language.'),
            'category_not_leaf' : _('Please select the other category')
            }

    errors_dict = {}

    def _to_python(self, value, state):
        if not ((value['name_ru'] and value['description_ru']) or (value['name_en'] and value['description_en']) or (value['name_uk'] and value['description_uk'])):
            self.errors_dict['fields_empty'] = self.message("fields_empty", '')
            raise Invalid(self.message("fields_empty", ''), value, state, error_dict=self.errors_dict)

        if not (value['name_ru'] and value['description_ru']):
            value['name_ru'] = ''
            value['description_ru'] = ''

        if not (value['name_en'] and value['description_en']):
            value['name_en'] = ''
            value['description_en'] = ''

        if not (value['name_uk'] and value['description_uk']):
            value['name_uk'] = ''
            value['description_uk'] = ''

        cat = CategoryModel().get_by_id(int(value['category_id']))
        if int(cat.is_leaf) != 1:
            self.errors_dict['category_not_leaf'] = self.message("category_not_leaf",'')
            raise Invalid(self.message("category_not_leaf", ''), value, state, error_dict=self.errors_dict)
        

        return value
