from decorator import decorator
from pylons import request
from pylons.controllers.util import abort

def user_is_authenticated():
    identity = request.environ.get('repoze.who.identity')
    return identity is not None

@decorator
def authenticated(func, *args, **kwargs):
    if not user_is_authenticated():
        abort(401)
    return func(*args, **kwargs)
