
__revision__  = "$Revision$"
__date__      = "$Date$"
__copyright__ = "Copyright (c) 2002 Open Source Applications Foundation"
__license__   = "http://osafoundation.org/Chandler_0.1_license_terms.htm"

import sys, re, xmlrpclib, jabber

from xml.sax import parseString
from SOAPpy import SOAPProxy
from repository.util.UUID import UUID
from repository.persistence.Repository import Store


class Transport(Store):
    pass


class SOAPTransport(Transport):

    def __init__(self, url):
        super(SOAPTransport, self).__init__()
        self.url = url

    def open(self):
        self.server = SOAPProxy(self.url)

    def close(self):
        pass
        
    def loadItem(self, uuid):
        return self.server.loadItem(uuid)

    def loadChild(self, parent, name):
        return self.server.loadChild(parent, name)

    def parseDoc(self, doc, handler):
        parseString(doc, handler)
        
    def getDocUUID(self, doc):
        index = doc.index('uuid=') + 6
        return UUID(doc[index:doc.index('"', index)])
    
    def getDocVersion(self, doc):
        index = doc.index('version=') + 9
        return long(doc[index:xml.index('"', index)])
    

class JabberTransport(Transport, jabber.Client):

    def __init__(self, me, password, you):

        names = re.compile("([^@]+)@([^/]+)(/(.*))?").match(me)

        Transport.__init__(self)
        jabber.Client.__init__(self, host=names.group(2))
        
        self.username = names.group(1)
        self.password = password
        self.resource = names.group(4) or 'client'
        self.iqTo = you

    def open(self):

        self.connect()
        if not self.auth(self.username, self.password, self.resource):
            self.disconnect()
            raise ValueError, "Auth failed %s %s" %(self.lastErr,
                                                    self.lastErrCode)

    def close(self):

        self.disconnect()

    def loadItem(self, uuid):

        iq = jabber.Iq(to=self.iqTo, type='get')

        iq.setQuery('jabber:iq:rpc')
        iq.setID(UUID().str64())
        iq.setQueryPayload(xmlrpclib.dumps((uuid.str64(),), 'loadItem'))

        self.send(iq)
        response = self.waitForResponse(iq.getID())

        if response is None:
            raise ValueError, self.lastErr

        xml = response.getQueryPayload()
        if xml.name == 'none':
            return None
        if xml.name == 'error':
            raise ValueError, xml.data

        return xml

    def loadChild(self, parent, name):

        iq = jabber.Iq(to=self.iqTo, type='get')

        iq.setQuery('jabber:iq:rpc')
        iq.setID(UUID().str64())
        iq.setQueryPayload(xmlrpclib.dumps((parent.str64(),
                                            name.encode('utf-8')),
                                           'loadChild'))

        self.send(iq)
        response = self.waitForResponse(iq.getID())

        if response is None:
            raise ValueError, self.lastErr

        xml = response.getQueryPayload()
        if xml.name == 'none':
            return None
        if xml.name == 'error':
            raise ValueError, xml.data

        return xml

    def parseDoc(self, doc, handler):

        def apply(node):

            handler.startElement(node.name, node.attrs)
            for kid in node.kids:
                apply(kid)
            for data in node.data:
                handler.characters(data)
            handler.endElement(node.name)
            
        handler.startDocument()
        apply(doc)
        handler.endDocument()

    def getDocUUID(self, doc):

        def apply(node):

            if node.name == 'item':
                return UUID(node.attrs['uuid'])
            for kid in node.kids:
                apply(kid)

        apply(doc)

    def getDocVersion(self, doc):

        def apply(node):

            if node.name == 'item':
                return long(node.attrs['version'])
            for kid in node.kids:
                apply(kid)

        apply(doc)
