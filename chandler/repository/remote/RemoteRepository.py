
__revision__  = "$Revision$"
__date__      = "$Date$"
__copyright__ = "Copyright (c) 2002 Open Source Applications Foundation"
__license__   = "http://osafoundation.org/Chandler_0.1_license_terms.htm"


from repository.persistence.XMLRepository import XMLRepository, XMLStore
from repository.persistence.XMLRepositoryView import XMLRepositoryView
from repository.remote.Transport import SOAPTransport, JabberTransport
from repository.remote.RemoteFilter import RemoteFilter


class RemoteRepository(XMLRepository):

    def __init__(self, dbHome, protocol, *args, **kwds):
        'Construct an RemoteRepository giving it a transport handler'
        
        super(RemoteRepository, self).__init__(dbHome)
        
        if protocol == 'soap':
            self.transport = SOAPTransport(self, *args, **kwds)
        elif protocol == 'jabber':
            self.transport = JabberTransport(self, *args, **kwds)
        else:
            raise NotImplementedError, '%s protocol' %(protocol)

    def _createStore(self):

        return RemoteStore(self, self.transport)
        
    def _createView(self):

        return RemoteRepositoryView(self)
    

class RemoteStore(XMLStore):

    def __init__(self, repository, transport):

        super(RemoteStore, self).__init__(repository)

        self.transport = transport
        self.remoteVersion = 0

    def open(self, create=False):

        super(RemoteStore, self).open(create=create)
        self.transport.open()

    def close(self):

        super(RemoteStore, self).close()
        self.transport.close()

    def loadItem(self, version, uuid):

        doc = super(RemoteStore, self).loadItem(version, uuid)
        if doc is None:
            doc = self.transport.serveItem(self.remoteVersion, uuid)
            if doc is not None:
                filter = RemoteFilter(self, version)
                self.transport.parseDoc(doc, filter)
                doc = filter.getDocument()
                self.remoteVersion = filter.version

        return doc

    def loadChild(self, version, uuid, name):

        doc = super(RemoteStore, self).loadChild(version, uuid, name)
        if doc is None:
            xml = self.transport.serveChild(self.remoteVersion, uuid, name)
            if xml is not None:
                filter = RemoteFilter(self, version)
                self.transport.parseDoc(xml, filter)
                doc = filter.getDocument()
                self.remoteVersion = filter.version

        return doc


class RemoteRepositoryView(XMLRepositoryView):

    def _loadItem(self, uuid):

        item = super(RemoteRepositoryView, self)._loadItem(uuid)
        if item is not None and self.version == 0:
            self.version = self.repository.store.getVersion()
            
        return item
        
    def _loadChild(self, parent, name):

        item = super(RemoteRepositoryView, self)._loadChild(parent, name)
        if item is not None and self.version == 0:
            self.version = self.repository.store.getVersion()

        return item
