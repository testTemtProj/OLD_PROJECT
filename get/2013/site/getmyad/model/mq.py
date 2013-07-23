# encoding: utf-8
'''
Created on Jul 20, 2010

@author: silver

'''
from amqplib import client_0_8 as amqp
from pylons import config

class MQ(object):
    '''
    Класс отвечает за отправку сообщений в RabbitMQ.
    '''


    def __init__(self):
        pass
    
    def _get_channel(self):
        ''' Подключается к брокеру mq '''
        conn = amqp.Connection(host=config.get('amqp_host', 'localhost'),
                               userid=config.get('amqp_user', 'guest'),
                               password=config.get('amqp_password', 'guest'),
                               insist=True)
        ch = conn.channel()
        ch.exchange_declare(exchange="getmyad", type="topic", durable=False, auto_delete=True)
        ch.exchange_declare(exchange="indexator", type="topic", durable=False, auto_delete=True)
        return ch

    def campaign_start(self, campaign_id):
        ''' Отправляет уведомление о запуске рекламной кампании ``campaign_id`` '''
        ch = self._get_channel()
        msg = amqp.Message(campaign_id)
        ch.basic_publish(msg, exchange='getmyad', routing_key='campaign.start')
        ch.basic_publish(msg, exchange='indexator', routing_key='campaign.update')
        ch.close()

    def campaign_stop(self, campaign_id):
        ''' Отправляет уведомление об остановке рекламной кампании ``campaign_id`` '''
        ch = self._get_channel()
        msg = amqp.Message(campaign_id)
        ch.basic_publish(msg, exchange='getmyad', routing_key='campaign.stop')
        ch.basic_publish(msg, exchange='indexator', routing_key='campaign.delete')
        ch.close()

    def campaign_update(self, campaign_id):
        ''' Отправляет уведомление об обновлении рекламной кампании ``campaign_id`` '''
        ch = self._get_channel()
        msg = amqp.Message(campaign_id)
        ch.basic_publish(msg, exchange='getmyad', routing_key='campaign.update')
        ch.basic_publish(msg, exchange='indexator', routing_key='campaign.update')
        ch.close()

    def informer_update(self, informer_id):
        ''' Отправляет уведомление о том, что информер ``informer_id`` был изменён '''
        ch = self._get_channel()
        msg = amqp.Message(informer_id)
        ch.basic_publish(msg, exchange='getmyad', routing_key='informer.update')
        ch.close()

    def account_update(self, login):
        ''' Отправляет уведомление об изменении в аккаунте ``login`` '''
        ch = self._get_channel()
        msg = amqp.Message(login)
        ch.basic_publish(msg, exchange='getmyad', routing_key='account.update')
        ch.close()

    def offer_delete(self, offer_Id, campaign_id):
        ''' Отправляет уведомление об удалении рекламного предложения '''
        ch = self._get_channel()
        msg = 'Offer:%s,Campaign:%s' % (offer_Id, campaign_id)
        msg = amqp.Message(msg)
        ch.basic_publish(msg, exchange='indexator', routing_key='advertise.delete')
        ch.close()


    def offer_add(self, offer_Id, campaign_id):
        '''Отправляет уведомление об добавлении рекламного предложения '''
        ch = self._get_channel()
        msg = 'Offer:%s,Campaign:%s' % (offer_Id, campaign_id)
        msg = amqp.Message(msg) 
        ch.basic_publish(msg, exchange='indexator', routing_key='advertise.update')
        ch.close()




