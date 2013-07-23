# coding: utf-8
import logging
import json
from datetime import datetime

from pylons import request, response, session, tmpl_context as c, url
from pylons.controllers.util import abort, redirect
from manager.lib import helpers as h

from manager.lib.base import BaseController, render
from manager.model.campaignsModel import CampaignsModel 
log = logging.getLogger(__name__)

class CampaignController(BaseController):
    
    def __before__(self):
        if not request.is_xhr:
            return abort(status_code=404)

    def __init__(self):
        self.campaigns_model = CampaignsModel


    def clear_all(self):
        campaigns_model = CampaignsModel
        campaigns_model.clear_all()
        return 'Все рекламные компании удалены с рынка'


    def state(self):
        campaign_id = request.params.get('campaign_id')
        #self.campaigns_model.get_campaign_status(campaign_id)

        
    def list(self):
        filters = json.loads(request.params.get('filter', '[]'))
        start = request.params.get('start', 0)
        limit = request.params.get('limit', 20)
        search_pattern = request.params.get('pattern')
        by = request.params.get('sort', 'title')
        direction = request.params.get('dir', 'ASC')
        if direction == 'ASC':
            direction = 1
        else:
            direction = -1
        
        campaigns = self.campaigns_model.get_all(skip=start, limit=limit, by=by, direction=direction, search_pattern=search_pattern, filters=filters)
        count = campaigns['count']
        campaigns = campaigns['result']
        rows = []
        
        for campaign in campaigns:
            row = {}
            row['id'] = campaign['idAdvertise']
            row['title'] = campaign['title'] 
            row['user'] = campaign['user']
            row['state'] = campaign['state']
            row['approved'] = campaign['approved']            
            row['state_Adload'] = campaign['state_Adload']
            row['social'] = campaign['social'] if campaign.has_key('social') else False
            row['started'] = ''
            row['finished'] = ''
            row['statistics'] = ''
            row['last_update'] = campaign['last_update'].strftime('%d.%m.%Y<br/>%H:%M:%S') if 'last_update' in campaign else 'None'

            if 'state' in campaign:
                campaign_state = campaign['state']
                if 'started' in campaign_state:
                    row['started'] = campaign_state['started'].strftime('%d.%m.%Y<br/>%H:%M:%S') if isinstance(campaign['state']['started'], datetime) else 'None'
                    del row['state']['started']

                if 'finished' in campaign_state:
                    row['finished'] = campaign_state['finished'].strftime('%m.%d.%Y<br/>%H:%M:%S') if isinstance(campaign['state']['finished'], datetime) else 'None'
                    del row['state']['finished']

                if 'statistics' in campaign_state:
                    row['statistics'] = campaign_state['statistics']

            rows.append(row)

        return json.dumps({"total": str(count), "data": rows}, ensure_ascii=False, skipkeys=True)
    

    def approve(self):
        campaign_id = request.params.get('campaign_id')
        self.campaigns_model.approve_campaign(campaign_id)

   
    def prohibit(self):
        campaign_id = request.params.get('campaign_id')
        self.campaigns_model.prohibit_campaign(campaign_id)


    def start(self):
        campaign_id = request.params.get('campaign_id')
        #TODO сделать что-то с результатом
        print self.campaigns_model.start_campaign(campaign_id)
    

    def stop(self):
        campaign_id = request.params.get('campaign_id')
        #TODO сделать что-то с результатом
        print self.campaigns_model.stop_campaign(campaign_id)


    def update(self):
        campaign_id = request.params.get('campaign_id')
        #TODO сделать что-то с результатом
        print self.campaigns_model.update_campaign(campaign_id)
