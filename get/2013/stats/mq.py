# encoding: utf-8
from amqplib import client_0_8 as amqp

class MQ():

    def _get_channel(self):
        conn = amqp.Connection(host='localhost:5672', userid='guest', password='guest', virtual_host="/", insist=False)
        ch = conn.channel()
        ch.exchange_declare(exchange="indexator", type="topic", durable=False, auto_delete=True)
        return ch

    def rating_informer_update(self, guid):
        ch = self._get_channel()
        msg = amqp.Message(guid)
        ch.basic_publish(msg, exchange='indexator', routing_key='informer_rating.update')
        ch.close()

    def rating_informer_delete(self, guid):
        ch = self._get_channel()
        msg = amqp.Message(guid)
        ch.basic_publish(msg, exchange='indexator', routing_key='informer_rating.delete')
        ch.close()

    def offer_update(self, offer_Id, campaign_id):
        ch = self._get_channel()
        msg = 'Offer:%s,Campaign:%s' % (offer_Id, campaign_id)
        msg = amqp.Message(msg)
        ch.basic_publish(msg, exchange='indexator', routing_key='advertise.update')
        ch.close()
    
    def offer_delete(self, offer_Id, campaign_id):
        ch = self._get_channel()
        msg = 'Offer:%s,Campaign:%s' % (offer_Id, campaign_id)
        msg = amqp.Message(msg)
        ch.basic_publish(msg, exchange='indexator', routing_key='advertise.delete')
        ch.close()
