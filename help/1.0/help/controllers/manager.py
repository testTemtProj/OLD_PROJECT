import logging

from pylons import request, response, session, tmpl_context as c, url
from pylons.controllers.util import abort, redirect
from help.lib.base import BaseController, render
from help.lib import helpers as h

from help.model.Project import Project
from help.model.Rules import Rules
from help.model.About import About
from help.model.News import News
from help.model.Doc import Doc

import datetime
from pylons.decorators import jsonify
log = logging.getLogger(__name__)

class ManagerController(BaseController):

    def index(self):
        c.controller = 'manager'
        c.name = 'manager'
        return render('/manager/index.mako.html')

    def saveAbout(self):
        lang = request.GET.get('lang','ru')
        project_name = request.GET.get('project',None)
        project = Project(name=project_name, lang=lang)
        project.load()
        doc = Doc()
        doc.title = request.POST.get('title','')
        doc.description = request.POST.get('description','')
        doc.metakey = request.POST.get('metakey','')
        doc.content = request.POST.get('text','')
        doc.id = request.POST.get('id',None)
        project_about = About(project.id, project.langId)
        project_about.save(doc)

    @jsonify
    def loadAbout(self):
        lang = request.GET.get('lang','ru')
        project_name = request.GET.get('project',None)
        project = Project(name=project_name, lang=lang)
        project.load()
        result = {}
        project_about = About(project.id, project.langId)
        doc = project_about.returnOne()
        result['id'] = doc.id
        result['title'] = doc.title
        result['description'] = doc.description
        result['metakey'] = doc.metakey
        result['text'] = doc.content
        return result

    def loadAllRules(self):
        lang = request.GET.get('lang','ru')
        project_name = request.GET.get('project',None)
        project = Project(name=project_name, lang=lang)
        project.load()
        project_rules = Rules(project.id, project.langId)
        rules = project_rules.returnAll()
        data = []
        for item in rules:
            row = (item.id,
                   item.createDate.strftime("%Y-%m-%d %H:%M:%S"),
                   h.trim_by_words(item.content.replace('\r','').replace('\n',''), 100)
            )
            data.append(row)
        return h.jgridDataWrapper(data)
    
    @jsonify
    def loadRules(self):
        lang = request.GET.get('lang','ru')
        project_name = request.GET.get('project',None)
        doc_id  = request.GET.get('id',None)
        project = Project(name=project_name, lang=lang)
        project.load()
        project_rules = Rules(project.id, project.langId)
        doc = project_rules.returnOne(id=doc_id)['doc']
        result = {}
        result['id'] = doc.id
        result['title'] = doc.title
        result['description'] = doc.description
        result['metakey'] = doc.metakey
        result['text'] = doc.content
        return result

    def saveRules(self):
        lang = request.GET.get('lang','ru')
        project_name = request.GET.get('project',None)
        project = Project(name=project_name, lang=lang)
        project.load()
        doc = Doc()
        doc.title = request.POST.get('title','')
        doc.description = request.POST.get('description','')
        doc.metakey = request.POST.get('metakey','')
        doc.content = request.POST.get('text','')
        doc.id = request.POST.get('id',None)
        project_rules = Rules(project.id, project.langId)
        project_rules.save(doc)

    def loadAllNews(self):
        lang = request.GET.get('lang','ru')
        project_name = request.GET.get('project',None)
        project = Project(name=project_name, lang=lang)
        project.load()
        project_news = News(project.id, project.langId)
        news = project_news.returnAll()
        data = []
        for item in news:
            row = (item.id,
                   item.createDate.strftime("%Y-%m-%d %H:%M:%S"),
                   h.trim_by_words(item.content.replace('\r','').replace('\n',''), 100)
            )
            data.append(row)
        return h.jgridDataWrapper(data)
    
    @jsonify
    def loadNews(self):
        lang = request.GET.get('lang','ru')
        project_name = request.GET.get('project',None)
        doc_id  = request.GET.get('id',None)
        project = Project(name=project_name, lang=lang)
        project.load()
        project_news = News(project.id, project.langId)
        doc = project_news.returnOne(id=doc_id)
        result = {}
        result['id'] = doc.id
        result['title'] = doc.title
        result['description'] = doc.description
        result['metakey'] = doc.metakey
        result['text'] = doc.content
        return result

    def saveNews(self):
        lang = request.GET.get('lang','ru')
        project_name = request.GET.get('project',None)
        project = Project(name=project_name, lang=lang)
        project.load()
        doc = Doc()
        doc.title = request.POST.get('title','')
        doc.description = request.POST.get('description','')
        doc.metakey = request.POST.get('metakey','')
        doc.content = request.POST.get('text','')
        doc.id = request.POST.get('id',None)
        project_news = News(project.id, project.langId)
        project_news.save(doc)
