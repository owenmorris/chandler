
__revision__  = "$Revision$"
__date__      = "$Date$"
__copyright__ = "Copyright (c) 2002 Open Source Applications Foundation"
__license__   = "http://osafoundation.org/Chandler_0.1_license_terms.htm"

import re

from model.persistence.Repository import OnDemandRepository, RepositoryError
from model.item.ItemRef import RefDict


class RemoteRepository(OnDemandRepository):

    def __init__(self, transport):
        'Construct an RemoteRepository giving it a transport handler'
        
        super(RemoteRepository, self).__init__(None)
        self._store = transport
        
    def create(self, verbose=False):

        if not self.isOpen():
            super(RemoteRepository, self).create(verbose)
            self._store.open()
            self._status |= self.OPEN

    def open(self, verbose=False, create=False):

        if not self.isOpen():
            super(RemoteRepository, self).open(verbose, create)
            self._store.open()
            self._status |= self.OPEN

    def close(self, purge=False):

        if self.isOpen():
            self._store.close()
            self._status &= ~self.OPEN

    def purge(self):
        pass

    def commit(self, purge=False, verbose=False):
        pass
    
    def createRefDict(self, item, name, otherName, ordered=False):

        return RefDict(item, name, otherName, ordered)
    
    def addTransaction(self, item):

        if not self.isOpen():
            raise RepositoryError, 'Repository is not open'

        return not self.isLoading()
