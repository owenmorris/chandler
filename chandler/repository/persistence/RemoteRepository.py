
__revision__  = "$Revision$"
__date__      = "$Date$"
__copyright__ = "Copyright (c) 2002 Open Source Applications Foundation"
__license__   = "http://osafoundation.org/Chandler_0.1_license_terms.htm"

import re

from repository.persistence.Repository import OnDemandRepository
from repository.persistence.Repository import RepositoryError
from repository.persistence.Repository import OnDemandRepositoryView
from repository.item.ItemRef import RefDict
from repository.util.ClassLoader import ClassLoader


class RemoteRepository(OnDemandRepository):

    def __init__(self, transport):
        'Construct an RemoteRepository giving it a transport handler'
        
        super(RemoteRepository, self).__init__(None)
        self._transport = transport
        
    def create(self, verbose=False):

        raise NotImplementedError, "RemoteRepository.create"

    def open(self, verbose=False, create=False):

        if create:
            raise NotImplementedError, "RemoteRepository.open(create)"
        
        if not self.isOpen():
            super(RemoteRepository, self).open(verbose)
            module, className = self._transport.open()
            self.viewClass = ClassLoader.loadClass(className, module)
            self._status |= self.OPEN

    def close(self, purge=False):

        if self.isOpen():
            self._transport.close()
            self._status &= ~self.OPEN

    def call(self, store, method, *args):

        return self._transport.call(store, method, *args)

    def _createView(self):

        return self.viewClass(self)

