from decorator import decorator
from pylons import  request, response
from pylons.controllers.util import abort
from repoze.who.interfaces import IAuthenticator, IMetadataProvider
from catalog.model.modelBase import Base
from pylons.controllers.util import redirect

import hashlib
import base64

db = Base.users
salt = 'secret_salt_fo`every_one'.encode('utf-8')


def user_is_auth():

    identity = request.environ.get('repoze.who.identity')
    return identity## is not None

def rem_user(name):
    global db
    db.remove({"user_name":name})
    return True

def upd_user(user):
    global db,salt

    hashed = hashlib.md5(user['password'])
    h_salt = hashlib.sha1(salt)
    check = hashed.hexdigest() + h_salt.hexdigest()
    db.update({"user_name":user['user_name']},{'$set':{"password": check.encode('utf-8'), "is_adm":user['is_adm']}})
    return True
    


def add_user(user):
    global db, salt

    #is_adm = True if user['is_adm'] == 'on' else False

    if db.find_one({'user_name':user['user_name']}):
        return False
    hashed = hashlib.md5(user['password'])
    h_salt = hashlib.sha1(salt)
    check = hashed.hexdigest() + h_salt.hexdigest()
    db.save({"user_name": user["user_name"], "password": check.encode('utf-8'), "is_adm":user['is_adm']})
    return True


@decorator
def auth(func, *args, **kwargs):
    if not user_is_auth():
        return abort(401)
    return func(*args, **kwargs)

def validate_password(user, password):
    return user['password'] == password

class MongoAuthenticatorPlugin(object):
    def authenticate(self, environ, identity):
        global db,salt
        if not ('login' in identity and 'password' in identity):
            return None 
        login = base64.b64decode(identity.get('login'))
        user = db.find_one({'user_name':login})
        h_salt = hashlib.sha1(salt)
        check =   identity.get('password') + h_salt.hexdigest().encode('utf8')
        if user and validate_password(user, check.encode('utf-8')):
            return identity['login']

class MongoUserMDPlugin(object):
    def add_metadata(self, environ, identity):
        global db
        user_data = {'user_name':identity['repoze.who.userid']}
        identity['user'] = db.find_one(user_data)
        return identity

class InsecureCookiePlugin(object):

    def __init__(self):
        self.cookie_name = 'logins'

    def identify(self, environ):
        from paste.request import get_cookies
        cookies = get_cookies(environ)
        cookie = cookies.get(self.cookie_name)

        if cookie is None:
            return None

        auth = cookie.value
        try:
            login, password = auth.split(':', 1)
            hashed_passwd = hashlib.md5(password)

            return {'login':login, 'password':password}
        except ValueError: # not enough values to unpack
            return None

    def remember(self, environ, identity):
        cookie_value = '%(login)s:%(password)s' % identity
        from paste.request import get_cookies
        cookies = get_cookies(environ)
        existing = cookies.get(self.cookie_name)
        value = getattr(existing, 'value', None)
        
        if value != cookie_value:
            set_cookies = '%s=%s; Path=/;' % (self.cookie_name, cookie_value)
            return [('Set-Cookie', set_cookies)]

    def forget(self, environ, identity):
        expired = ('%s=""; Path=/; Expires=Sun, 10-May-1971 11:59:00 GMT' %
                   self.cookie_name)
        return [('Set-Cookie', expired)]

    def __repr__(self):
        return '<%s %s>' % (self.__class__.__name__, id(self))
