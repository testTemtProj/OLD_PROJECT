
from pymongo.connection import Connection, _str_to_node
from pymongo.master_slave_connection import MasterSlaveConnection
from pymongo.errors import AutoReconnect,DuplicateKeyError,CollectionInvalid

import time
import functools

# validate slaves every 5 minutes
VALIDATE_INTERVAL = 5 * 60

class ClusterConnection(MasterSlaveConnection):
  def __init__(self, *args, **kwargs):
    super(ClusterConnection,self).__init__(*args, **kwargs)
    self._last_validate_time = time.time()

  # This is a good time to overload the tz_aware property if the default value of
  # True doesn't work for your use.
  @property
  def tz_aware(self):
    return False

  def validate_slaves(self, slave_uris):
    '''
    If we're at the check interval, confirm that all slaves are connected to their
    intended hosts and if not, reconnect them.
    '''
    if time.time()-self._last_validate_time < VALIDATE_INTERVAL: return
    
    hosts_ports = [_str_to_node(uri) for uri in slave_uris]

    # Walk a copy of the current slave list so that we can manipulate it. For
    # each connection that is not pointing to a configured slave, disconnect
    # it and remove from the list.
    for slave in self.slaves[:]:
      host_port = (slave._Connection__host, slave._Connection__port)
      if host_port not in hosts_ports:
        slave.disconnect()
        self.slaves.remove( slave )
      else:
        hosts_ports.remove( host_port )

    # For all hosts where there wasn't an existing connection, create one
    for host,port in hosts_ports:
      self.slaves.append( Connection(
        host=host, port=port, slave_okay=True, _connect=False) )

    self._last_validate_time = time.time()

def with_reconnect(func):
  '''
  Handle when AutoReconnect is raised from pymongo. This is the standard error
  raised for everything from "host disconnected" to "couldn't connect to host"
  and more.

  The sleep handles the edge case when the state of a replica set changes, and
  the cursor raises AutoReconnect because the master may have changed. It can
  take some time for the replica set to stop raising this exception, and the 
small sleep and iteration count gives us a couple of seconds before we fail
completely. See also http://jira.mongodb.org/browse/PYTHON-216
  '''
  @functools.wraps(func)
  def _reconnector(*args, **kwargs):
    for x in xrange(0,20):
      try:
        return func(*args, **kwargs)
      except AutoReconnect:
        time.sleep(0.250)
        pass
    raise
  return _reconnector

class ApplicationDatabaseInterface(object):
  '''
  An example of a class you'd use for interfacing with the database.
  '''

  def __init__(self, *args, **kwargs):
    self._connection = None
    self._hosts = kwargs.get('hosts')  # a list of all hosts including the master

  @with_reconnect
  def query(self, q):
    conn = self.connection()
    # TODO: perform the query

  def connection(self):
    '''
    Get the current connection to use for the transaction. Opens new connection 
    if there isn't on already.
    '''
    rval = self._connection
    if not rval:
      rval = ClusterConnection(
        Connection( self._hosts ),
        [Connection(host, slave_okay=True, _connect=False) for host in self._hosts]
      )
    else:
      rval.validate_slaves( self._hosts )
    return rval
