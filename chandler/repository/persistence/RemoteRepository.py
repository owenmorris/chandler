
__revision__  = "$Revision$"
__date__      = "$Date$"
__copyright__ = "Copyright (c) 2002 Open Source Applications Foundation"
__license__   = "http://osafoundation.org/Chandler_0.1_license_terms.htm"

import re

from repository.persistence.Repository import OnDemandRepository
from repository.persistence.Repository import RepositoryError
from repository.persistence.Repository import OnDemandRepositoryView
from repository.item.ItemRef import RefDict


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

    def _createView(self):

        return RemoteRepositoryView(self)


class RemoteRepositoryView(OnDemandRepositoryView):
    
    def commit(self, purge=False, verbose=False):
        pass
    
    def createRefDict(self, item, name, otherName, persist):

        return RefDict(item, name, otherName)
