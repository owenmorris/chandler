
__revision__  = "$Revision$"
__date__      = "$Date$"
__copyright__ = "Copyright (c) 2004 Open Source Applications Foundation"
__license__   = "http://osafoundation.org/Chandler_0.1_license_terms.htm"

import sys, re, xmlrpclib, jabber

from libxml2 import createPushParser
from SOAPpy import SOAPProxy

from repository.util.UUID import UUID


class RemoteError(ValueError):
    pass


class Transport(object):

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
            return value.decode('base64').decode('zlib')
        if c == 'u':
            if value == 'None':
                return None
            return UUID(value)
        if c == 's':
            return value
        if c == 'i':
            return long(value)

        if c == 't':
            values = []
            for i in xrange(len(value)):
                values.append(self.decode(returnType, i + 1, value[i]))
            return tuple(values)

        raise TypeError, '%s: unsupported signature char' %(c)

    def parseDoc(self, doc, handler):

        createPushParser(handler, doc, len(doc), "item").parseChunk('', 0, 1)
        if handler.errorOccurred():
            raise handler.saxError()
        
    def getVersionInfo(self):

        return self.call('getVersionInfo', 'tui')

    def serveItem(self, version, uuid):

        return self.call('serveItem', 'x', version, uuid)
    
    def serveChild(self, version, uuid, name):

        return self.call('serveChild', 'x', version, uuid, name)


class SOAPTransport(Transport):

    def __init__(self, repository, url):

        super(SOAPTransport, self).__init__(repository)
        self.url = url

    def open(self):

        self.server = SOAPProxy(self.url, encoding='utf-8')

    def _call(self, method, *args):

        try:
            return self.server.call(method, *args)
        except Exception, e:
            raise
#            raise RemoteError, str(e)

    def close(self):
        pass

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

    def open(self):

        self.connect()
        if not self.auth(self.username, self.password, self.resource):
            self.disconnect()
            raise ValueError, "Auth failed %s %s" %(self.lastErr,
                                                    self.lastErrCode)

    def close(self):

        self.disconnect()

    def decode(self, returnType, offset, value):

        if value is not None and returnType[offset] == 'x':
            value = value.encode('utf-8').replace('@', '\n')

        return Transport.decode(self, returnType, offset, value)
    
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
