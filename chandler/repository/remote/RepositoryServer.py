
__revision__  = "$Revision$"
__date__      = "$Date$"
__copyright__ = "Copyright (c) 2004 Open Source Applications Foundation"
__license__   = "http://osafoundation.org/Chandler_0.1_license_terms.htm"


import sys, re, xmlrpclib, jabber
from SOAPpy import SOAPServer
from chandlerdb.util.uuid import UUID


class RepositoryServer(object):

    def __init__(self, repository):

        super(RepositoryServer, self).__init__()
        self.repository = repository

    def startup(self):
        raise NotImplementedError, 'RepositoryServer.startup'

    def terminate(self):
        raise NotImplementedError, 'RepositoryServer.terminate'

    def call(self, method, signature, *args):

        store = self.repository.store
        try:
            args = self.decode(signature, args)
            value = getattr(type(store), method)(store, *args)
            value = self.encode(signature, 0, value)

            return value
        except Exception:
            self.repository.logger.exception('RepositoryServer')
            raise

    def decode(self, signature, args):

        result = []
        count = len(args)
        offset = len(signature) - count

        for i in xrange(count):
            c = signature[i + offset]
            arg = args[i]

            if c == 'x':
                result.append(arg)
            elif c == 'u':
                result.append(UUID(arg))
            elif c == 's':
                result.append(unicode(arg, 'utf-8'))
            elif c == 'i':
                result.append(long(arg))
            else:
                raise TypeError, '%s: unsupported signature char' %(c)

        return result

    def encode(self, signature, offset, value):

        if value is None:
            return None
        
        c = signature[offset]
        
        if c == 'x':
            return value.encode('zlib').encode('base64')
        if c == 'u':
            return value.str64()
        if c == 's':
            return value
        if c == 'i':
            return str(value)

        if c == 't':
            values = []
            offset += 1
            for i in xrange(len(value)):
                values.append(self.encode(signature, i + offset, value[i]))
            return tuple(values)

        raise TypeError, '%s: unsupported signature char' %(c)


class SOAPRepositoryServer(RepositoryServer):

    def __init__(self, repository, host='localhost', port=8080):

        super(SOAPRepositoryServer, self).__init__(repository)

        self.server = SOAPServer((host, port), encoding='utf-8')
        self.server.registerObject(self)

    def startup(self):

        self.server.serve_forever()


class JabberRepositoryServer(RepositoryServer, jabber.Client):

    def __init__(self, repository, me, password):

        names = re.compile("([^@]+)@([^/]+)(/(.*))?").match(me)

        RepositoryServer.__init__(self, repository)
        jabber.Client.__init__(self, host=names.group(2))
        
        self.username = names.group(1)
        self.password = password
        self.resource = names.group(4) or 'client'

    def startup(self):

        self.connect()
        try:
            if not self.auth(self.username, self.password, self.resource):
                raise ValueError, "Auth failed %s %s" %(self.lastErr,
                                                        self.lastErrCode)

            self.setIqHandler(self.iqHandler, type='get', ns='jabber:iq:rpc')

            self.running = True
            while self.running:
                self.process(1)
        finally:
            self.disconnect()

    def terminate(self):

        self.running = False

    def open(self):

        return "<value><![CDATA[%s]]></value>" %(super(JabberRepositoryServer,
                                                       self).open())

    def call(self, method, signature, *args):

        value = super(JabberRepositoryServer, self).call(method, signature,
                                                         *args)
        if value is None:
            return "<none/>"
        
        c = signature[0]

        if c == 'i':
            return "<value>%s</value>" %(value)
        if c == 't':
            return "<values>%s</values>" %("".join(['<value><![CDATA[%s]]></value>' %(v) for v in value]))

        if c == 'x':
            value = value.replace('\n', '@')

        return "<value><![CDATA[%s]]></value>" %(value)

    def iqHandler(self, iq):

        xmlrpc = iq.getQueryPayload()
        args, func = xmlrpclib.loads("<?xml version='1.0'?>%s" %(xmlrpc))

        try:
            method = getattr(JabberRepositoryServer, func, None)
            if method:
                result = method(self, *args)
            else:
                result = "<error>No such method: %s</error>" %(func)
        except Exception, e:
            self.repository.logger.exception('RepositoryServer')
            result = "<error><![CDATA[%s]]></error>" %(e)

        iq.setQueryPayload(result)
        iq.setType('set')
        iq.setTo(iq.getFrom())
        
        self.send(iq)
