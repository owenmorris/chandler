
__revision__  = "$Revision$"
__date__      = "$Date$"
__copyright__ = "Copyright (c) 2002 Open Source Applications Foundation"
__license__   = "http://osafoundation.org/Chandler_0.1_license_terms.htm"

import sys, re, xmlrpclib, jabber

from xml.sax import parseString
from SOAPpy import SOAPProxy
from repository.util.UUID import UUID
from repository.persistence.Repository import Store

class RemoteError(ValueError):
    pass


class Transport(Store):

    def call(self, method, returnType, *args):

        signature, args = self.encode(returnType, args)
        value = self._call(method, signature, *args)

        return self.decode(returnType, 0, value)

    def encode(self, returnType, args):

        signature = [returnType]
        result = []
        for arg in args:
            if isinstance(arg, UUID):
                signature.append('u')
                result.append(arg.str64())
            elif isinstance(arg, unicode):
                signature.append('s')
                result.append(arg.encode('utf-8'))
            elif isinstance(arg, long) or isinstance(arg, int):
                signature.append('i')
                result.append(str(arg))
            else:
                signature.append('x')
                result.append(arg)

        return ("".join(signature), result)
    
    def decode(self, returnType, offset, value):

        if value is None:
            return None

        c = returnType[offset]

        if c == 'x':
            return value
        if c == 'd':
            return value
        if c == 'u':
            if value == 'None':
                return None
            return UUID(value)
        if c == 's':
            return unicode(value, 'utf-8')
        if c == 'i':
            return long(value)

        if c == 't':
            values = []
            for i in xrange(len(value)):
                values.append(self.decode(returnType, i + 1, value[i]))
            return tuple(values)

        raise TypeError, '%s: unsupported signature char' %(c)

    def getVersion(self):

        return self.call('getVersion', 'i')

    def loadItem(self, version, uuid):

        return self.call('loadItem', 'd', version, uuid)
    
    def loadChild(self, version, uuid, name):

        return self.call('loadChild', 'd', version, uuid, name)

    def loadRoots(self, version):

        self.call('loadRoots', 'x', version)

    def loadRef(self, version, uItem, uuid, key):

        return self.call('loadRef', 'tuuuux', version, uItem, uuid, key)


class SOAPTransport(Transport):

    def __init__(self, repository, url):

        super(SOAPTransport, self).__init__(repository)
        self.url = url

    def open(self, create=False):

        self.server = SOAPProxy(self.url)
        return self.server.open()

    def _call(self, method, *args):

        try:
            return self.server.call(method, *args)
        except Exception, e:
            raise RemoteError, str(e)

    def close(self):
        pass

    def parseDoc(self, doc, handler):

        parseString(doc, handler)
        
    def getDocUUID(self, doc):

        index = doc.index('uuid=') + 6
        return UUID(doc[index:doc.index('"', index)])
    
    def getDocVersion(self, doc):

        index = doc.index('version=') + 9
        return long(doc[index:xml.index('"', index)])


class JabberTransport(Transport, jabber.Client):

    def __init__(self, repository, me, password, you):

        names = re.compile("([^@]+)@([^/]+)(/(.*))?").match(me)

        Transport.__init__(self, repository)
        jabber.Client.__init__(self, host=names.group(2))
        
        self.username = names.group(1)
        self.password = password
        self.resource = names.group(4) or 'client'
        self.iqTo = you

    def open(self, create=False):

        self.connect()
        if not self.auth(self.username, self.password, self.resource):
            self.disconnect()
            raise ValueError, "Auth failed %s %s" %(self.lastErr,
                                                    self.lastErrCode)

        return self._call_('open')

    def close(self):

        self.disconnect()

    def _call(self, method, *args):

        return self._call_('call', method, *args)

    def _call_(self, method, *args):
        
        iq = jabber.Iq(to=self.iqTo, type='get')

        iq.setQuery('jabber:iq:rpc')
        iq.setID(UUID().str64())
        iq.setQueryPayload(xmlrpclib.dumps(args, method))

        self.send(iq)
        response = self.waitForResponse(iq.getID())

        if response is None:
            raise ValueError, self.lastErr

        xml = response.getQueryPayload()
        if xml.name == 'value':
            return "".join(xml.data)
        if xml.name == 'values':
            return tuple(["".join(kid.data) for kid in xml.kids])
        if xml.name == 'none':
            return None
        if xml.name == 'error':
            raise RemoteError, "".join(xml.data)

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
