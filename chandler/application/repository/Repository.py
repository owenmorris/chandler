""" Repository, a persistent collection of Things.

    @@@ Uses ZODB to persist Things. Currently just a
    scaffolding implementation.
"""

__revision__ = "$Revision$"
__date__ = "$Date$"
__copyright__ = "Copyright (c) 2003 Open Source Applications Foundation"
__license__ = "http://osafoundation.org/Chandler_0.1_license_terms.htm"

from persistence import Persistent
from persistence.dict import PersistentDict
from persistence.list import PersistentList

import transaction
from zodb import db
from zodb.storage.file import FileStorage

from application.repository import Thing

class Repository:

    # as per the borg pattern, this will become the object's __dict__
    _shared_state = {}
    
    _storage = FileStorage('_Repository_')
    _db = db.DB(_storage)
    _connection = _db.open()
    _dbroot = _connection.root()

    if not _dbroot.has_key('thingList'):
        _dbroot['thingList'] = PersistentList()
    _shared_state['thingList'] = _dbroot['thingList']
    
    transaction.get_transaction().commit()
    
    def __init__(self):
        self.__dict__ = self._shared_state
        
    def AddThing(self, thing):
        """ Add the 'thing' to the repostiory """
        assert(isinstance(thing, Thing.Thing))
        self.thingList.append(thing)
        transaction.get_transaction().commit()

    def DeleteThing(self, thing):
        """ Delete the 'thing' from the repository
        """
        try:
            index = self.thingList.index(thing)
            del self.thingList[index]
        except:
            # FIXME: need to indicate failure somehow...
            pass
        
    def FindThing(self, url):
        for thing in self.thingList:
            if (thing.GetURL() == url):
                return thing
        return None
        
    def Commit(self):
        """ Commit all ZODB changes.
        """
        transaction.get_transaction().commit()
        
    def PrintTriples(self):
        """ Print the entire collection of things as triples.
        """
        for thing in self.thingList:
            thing.PrintTriples()
        
