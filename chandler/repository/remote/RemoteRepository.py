
__revision__  = "$Revision$"
__date__      = "$Date$"
__copyright__ = "Copyright (c) 2004 Open Source Applications Foundation"
__license__   = "http://osafoundation.org/Chandler_0.1_license_terms.htm"


from repository.persistence.DBRepository import DBRepository, XMLStore
from repository.persistence.DBRepositoryView import DBRepositoryView
from repository.remote.Transport import SOAPTransport, JabberTransport
from repository.remote.RemoteFilter import RemoteFilter
from chandlerdb.util.UUID import UUID


class RemoteRepository(DBRepository):

    def __init__(self, dbHome, protocol, cloudAlias, *args, **kwds):
        'Construct an RemoteRepository giving it a transport handler'
        
        super(RemoteRepository, self).__init__(dbHome)
        
        if protocol == 'soap':
            self.transport = SOAPTransport(self, *args, **kwds)
        elif protocol == 'jabber':
            self.transport = JabberTransport(self, *args, **kwds)
        else:
            raise NotImplementedError, '%s protocol' %(protocol)

        self.cloudAlias = cloudAlias

    def _createStore(self):

        return RemoteStore(self, self.transport)
    

class RemoteStore(XMLStore):

    def __init__(self, repository, transport):

        super(RemoteStore, self).__init__(repository)
        self.transport = transport

    def open(self, **kwds):

        super(RemoteStore, self).open(**kwds)
        self.transport.open()

    def close(self):

        super(RemoteStore, self).close()
        self.transport.close()

    def loadItem(self, version, uuid):

        doc = super(RemoteStore, self).loadItem(version, uuid)
        if doc is None:
            v, versionId = self._values.getVersionInfo(self.itsUUID)
            remoteVersion = self._values.getVersion(versionId)
            xml = self.transport.serveItem(remoteVersion, uuid,
                                           self.repository.cloudAlias)
            if xml is not None:
                filter = RemoteFilter(self, versionId)
                self.transport.parseDoc(xml, filter)
                doc = filter.getDocument()

        return doc

    def getVersion(self):

        version = super(RemoteStore, self).getVersion()
        values = self._values
        
        if version == 0:
            versionId, version = self.transport.getVersionInfo()

            txnStatus = 0
            try:
                txnStatus = self.startTransaction()
                values.setVersion(version)
                values.setVersion(version, versionId)
                values.setVersionId(versionId, self.itsUUID)
            except:
                self.abortTransaction(txnStatus)
                raise
            else:
                self.commitTransaction(txnStatus)
                
        return version

    itsUUID = UUID('200a5564-a60f-11d8-fb65-000393db837c')
