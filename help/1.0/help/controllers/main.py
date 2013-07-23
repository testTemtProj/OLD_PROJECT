import logging
from pylons import request, response, session, tmpl_context as c, url
from pylons.controllers.util import abort, redirect
from help.lib.base import BaseController, render
from help.model.Project import Project
from help.model.Rules import Rules
from help.model.About import About

import datetime

log = logging.getLogger(__name__)

class MainController(BaseController):
    def __before__(self):
        self.project = Project(url.environ['pylons.routes_dict']['controller'])
        self.project.load()
        c.name = self.project.name
        c.controller = self.project.controller

    def index(self):
        return render('/main/index.mako.html')

    def about(self):
        project_about = About(self.project.id, self.project.langId)
        doc = project_about.returnOne()
        c.content = doc.content
        return render('/main/about.mako.html')

    def rules(self,date=None):
        project_rules = Rules(self.project.id, self.project.langId)
        if date != None:
            date = datetime.datetime.strptime(date, "%Y-%m-%d-%H-%M-%S")
            rule = project_rules.returnOne(date)
        else:
            rule = project_rules.returnOne()
        c.content = rule['doc'].content
        c.oldRules = rule['oldRules']
        return render('/main/rules.mako.html')

    def search(self):
        return render('/main/search.mako.html')

    def news(self):
        return render('/main/news.mako.html')

    def help(self):
        return render('/main/help.mako.html')

    def lang(self):
        if 'lang' in request.GET and request.GET['lang'] in ['ru','en','uk']:
            session['lang'] = request.GET['lang']
            session.save()
