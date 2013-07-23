# coding: utf-8
from celery.decorators import task
from datetime import datetime
from email.MIMEText import MIMEText
import email.Charset
import os
import ConfigParser
import pymongo
import smtplib
email.Charset.add_charset('utf-8', email.Charset.SHORTEST, None, None)     # Для отправки писем в UTF-8, можно будет убрать в Python 2.7    

# Если pylons.config недоступен, пытаемся имитировать его
try:
    from pylons import config
    assert config['pylons.app_globals']
except (ImportError, AssertionError):
    PYLONS_CONFIG = "deploy.ini"
    current_dir = os.path.dirname(__file__)
    base_dir = os.path.join(current_dir, '../../')
    config_file = os.path.join(base_dir, PYLONS_CONFIG)
    cp = ConfigParser.ConfigParser({'here': base_dir})
    cp.read(config_file)
    config = {}
    for option in cp.options('app:main'):
        config[option] = cp.get('app:main', option)

# Подключение к MongoDB       
try:
    from pylons import app_globals
    db = app_globals.db 
except:
    try:
        mongo_connection = pymongo.Connection(host=config.get('mongo_host', 'localhost'))
        db = mongo_connection[config.get('mongo_database', 'getmyad_db')]
    except:
        print "error connecting to mongo!"
        db = None


SENDER_YOTTOS_SUPPORT = 'support'

def sendmail(email_to, subject, body, sender=SENDER_YOTTOS_SUPPORT):
    ''' Отправка сообщения по электронной почте.
    
        По возможности (при рабочем celery и rabbitmq) используется
        отложенная отправка писем. 
    
        Все отправленные сообщения сохраняются в коллекции ``log.email``.
        
        При ошибке предпринимается ``max_retries`` попыток повторной отправки письма
        с интервалом в ``default_retry_delay`` секунд.
    
        ``email_to`` это адрес получателя письма, параметр должен быть строкой или списком.
        
        ``subject`` --- тема письма.
        
        ``body`` --- тело письма.
        
        ``sender`` -- отправитель письма. На данный момент поддерживается только значение
        SENDER_YOTTOS_SUPPORT --- e-mail службы поддержки Yottos.
    ''' 
    try:
        _sendmail_task.delay(email_to, subject, body, sender)
    except:
        print "Delayed execution failed, trying to send mail right now"
        _sendmail_worker(email_to, subject, body, sender)

        
def _sendmail_worker(email_to, subject, body, sender, **kwargs):
    ''' Выполняет всю работу по отправке почты. В случае ошибок бросает Exception '''
    # параметры SMTP-сервера
    if sender == SENDER_YOTTOS_SUPPORT:
        server = config.get('support_smtp_server')
        port = config.get('support_smtp_port')
        user_name = config.get('support_smtp_username')
        user_passwd = config.get('support_smtp_password')
        sender_email = 'support@yottos.com'
    else:
        raise TypeError("Unknown 'sender' value: %s" % sender)
    
    if not isinstance(email_to, (basestring, list)):
        raise TypeError('email_to should be a string or tuple')
    
    msg = MIMEText(unicode(body), _charset='utf-8')
    msg['Subject'] = unicode(subject)
    msg['From'] = unicode(sender_email)
    msg['To'] = unicode(email_to)

    try:
        s = smtplib.SMTP(server, port)
        s.ehlo()
        s.login(user_name, user_passwd)
        s.sendmail(sender_email, email_to, msg.as_string())
        s.quit()
    except Exception as ex:
        db.log.email.insert({'subj': subject,
                             'to': email_to,
                             'from': sender_email,
                             'text': body, 
                             'date': datetime.today(),
                             'ok': False,
                             'exception': str(ex),
                             'retry': kwargs.get('task_retries', 0) },
                             safe=True)
        raise
    else:
        db.log.email.insert({'subj': subject,
                             'to': email_to,
                             'from': sender_email,
                             'text': body, 
                             'date': datetime.today(),
                             'ok': True},
                             safe=True)


@task(max_retries=10, default_retry_delay=3*60)
def _sendmail_task(email_to, subject, body, sender, **kwargs):
    ''' Задача Celery для отправки электронной почты.
        Значения параметров те же, что и у sendmail '''
    try:
        _sendmail_worker(email_to, subject, body, sender)
    except Exception as ex:
        print "sendmail failed to %s: %s (retry #%s)" % (email_to, ex, kwargs.get('task_retries',0))
        _sendmail_task.retry(args=[email_to, subject, body, sender],
                       kwargs=kwargs, exc=ex)
    else:
        print "sendmail to %s ok" % email_to
