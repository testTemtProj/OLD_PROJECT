#!/usr/bin/python
# -*- coding: UTF8 -*-

from amqplib import client_0_8 as amqp

# Подключиться к серверу

lConnection = amqp.Connection(host="localhost:5672", userid="guest", password="guest", virtual_host="/", insist=False)
lChannel = lConnection.channel()
#Создадим очередь для сообшений
#durable=True - пересоздаеться после перезагрузки RabbitMQ.
#exclusive=False - очередь видна всем а не только клиенту
#auto_delete=False - очередь останеться сушествовать после отключения клиента
lChannel.queue_declare(queue="myClientQueue", durable=True, exclusive=False, auto_delete=False)

#Создаем точку обмена
lChannel.exchange_declare(exchange="myExchange", type="direct", durable=True, auto_delete=False)

#Привязываем точку обмена к очереди
lChannel.queue_bind(queue="myClientQueue", exchange="myExchange", routing_key="Test")


 
# Создать сообщение
lMessage = amqp.Message("Test message!Создадим очередь для сообшенийdurable=True - пересоздаеться после перезагрузки RabbitMQ.exclusive=False - очередь видна всем а не только клиентуочередь останеться сушествовать после отключения клиента")

# Установить тип сообщение - persistant.  Означает, что он выживет перезагрузки RabbitMQ. 
lMessage.properties["delivery_mode"] = 2

# Опубликовать сообшение в точке обмена
i = 0
while i < 100000:
    lChannel.basic_publish(lMessage, exchange="myExchange", routing_key="Test")
    i += 1

# Закрыть соединение
lChannel.close()
lConnection.close()
