
__revision__  = "$Revision$"
__date__      = "$Date$"
__copyright__ = "Copyright (c) 2002 Open Source Applications Foundation"
__license__   = "http://osafoundation.org/Chandler_0.1_license_terms.htm"


from repository.persistence.Repository import OnDemandRepository
from repository.persistence.Repository import RepositoryError
from repository.persistence.Repository import OnDemandRepositoryView
from repository.persistence.Transport import SOAPTransport, JabberTransport
from repository.util.ClassLoader import ClassLoader


class RemoteRepository(OnDemandRepository):

    def __init__(self, protocol, *args, **kwds):
        'Construct an RemoteRepository giving it a transport handler'
        
        super(RemoteRepository, self).__init__(None)
        if protocol == 'soap':
            transport = SOAPTransport(self, *args)
        elif protocol == 'jabber':
            transport = JabberTransport(self, *args)
        else:
            raise NotImplementedError, '%s protocol' %(protocol)
        
        self.store = transport
        
    def create(self):

        raise NotImplementedError, "RemoteRepository.create"

    def open(self, create=False):

        if not self.isOpen():
            super(RemoteRepository, self).open()
            className = self.store.open(create)
            self.viewClass = ClassLoader.loadClass(className)
            self._status |= self.OPEN

    def close(self, purge=False):

        if self.isOpen():
            self.store.close()
            self._status &= ~self.OPEN

    def _createView(self):

        return self.viewClass(self)

