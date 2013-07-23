# coding: utf-8
from rynok.lib.base import BaseController, render
from pylons import request, response, session, tmpl_context as c, url
from pylons import app_globals

from rynok.model.categoriesModel import CategoriesModel
from rynok.model.settingsModel import SettingsModel

class MainController(BaseController):

    def __init__(self):
        BaseController.__init__(self)

    def index(self):        
        settings_model = SettingsModel
        c.cats = settings_model.get_main_page_categories()
        c.banner = settings_model.get_main_page_banner()
        return render('/main.mako.html')
