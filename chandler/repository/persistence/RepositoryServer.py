
__revision__  = "$Revision$"
__date__      = "$Date$"
__copyright__ = "Copyright (c) 2002 Open Source Applications Foundation"
__license__   = "http://osafoundation.org/Chandler_0.1_license_terms.htm"


import sys, re, xmlrpclib, jabber

from SOAPpy import SOAPServer

from repository.persistence.XMLRepository import XMLRepository
from repository.item.ItemRef import RefDict
from repository.util.UUID import UUID


class RepositoryServer(object):

    def __init__(self, repository):

        super(RepositoryServer, self).__init__()
        self.repository = repository

    def startup(self):
        raise NotImplementedError, 'RepositoryServer.startup'

    def terminate(self):
        raise NotImplementedError, 'RepositoryServer.terminate'

    def open(self):

        self._stores, viewClass = self.repository.serverOpen()
        return (viewClass.__module__, viewClass.__name__)

    def call(self, store, method, *args):

        store = self._stores[store]
        return getattr(type(store), method)(store, *args)


class SOAPRepositoryServer(RepositoryServer):

    def __init__(self, repository, host='localhost', port=8080):

        super(SOAPRepositoryServer, self).__init__(repository)

        self.server = SOAPServer((host, port))
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
        
    def iqHandler(self, iq):

        xmlrpc = iq.getQueryPayload()
        args, func = xmlrpclib.loads("<?xml version='1.0'?>%s" % xmlrpc)

        method = getattr(JabberRepositoryServer, func, None)
        if method:
            result = method(self, *args)
        else:
            result = "<error>%s</error>" %(func)

        if result is None:
            result = '<none/>'
            
        iq.setQueryPayload(result)
        iq.setType('set')
        iq.setTo(iq.getFrom())
        
        self.send(iq)
