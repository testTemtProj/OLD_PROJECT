import logging
from pylons import request, response, session, tmpl_context as c, url
from pylons.controllers.util import abort, redirect
from help.lib.base import BaseController, render
from help.model.Project import Project
from help.model.Rules import Rules
from help.model.About import About
from help.model.News import News

import datetime

log = logging.getLogger(__name__)

class ClevadController(BaseController):
    def __before__(self):
        self.project = Project(url.environ['pylons.routes_dict']['controller'])
        self.project.load()
        c.name = self.project.name
        c.controller = self.project.controller

    def index(self):
        return render('/clevad/index.mako.html')

    def about(self):
        project_about = About(self.project.id, self.project.langId)
        doc = project_about.returnOne()
        c.content = doc.content
        return render('/clevad/about.mako.html')

    def rules(self,date=None):
        project_rules = Rules(self.project.id, self.project.langId)
        if date != None:
            date = datetime.datetime.strptime(date, "%Y-%m-%d-%H-%M-%S")
            rule = project_rules.returnOne(date)
        else:
            rule = project_rules.returnOne()
        c.content = rule['doc'].content
        c.oldRules = rule['oldRules']
        return render('/clevad/rules.mako.html')

    def search(self):
        return render('/clevad/search.mako.html')

    def news(self,date=None):
        project_news = News(self.project.id, self.project.langId)
        if date != None:
            date = datetime.datetime.strptime(date, "%Y-%m-%d-%H-%M-%S")
            news = project_news.returnOne(date)
            c.content = news
        else:
            skip = request.GET.get('skip',0)
            limit = request.GET.get('limit',10)
            news = project_news.returnAll(skip,limit)
            c.content = news
        return render('/clevad/news.mako.html')

    def help(self):
        return render('/clevad/help.mako.html')
