from twisted.protocols.policies import ProtocolWrapper
from twisted.internet import defer
from M2Crypto import BIO, m2
from M2Crypto.SSL import Context, Connection

debug = 0

class TLSProtocolWrapper(ProtocolWrapper):
    """
    A SSL/TLS protocol wrapper to be used with Twisted.

    Usage:
        factory = MyFactory()
        factory.startTLS = True # Starts SSL immediately, otherwise waits
                                # for STARTTLS from peer (XXX TODO)
        wrappingFactory = WrappingFactory(factory)
        wrappingFactory.protocol = TLSProtocolWrapper
        reactor.connectTCP(host, port, wrappingFactory)

    MyFactory should have the following interface:

        startTLS:                boolean   Set to True to start SSL immediately
        getContext():            function  Should return M2Crypto.SSL.Context()
        sslPostConnectionCheck() function  Should do SSL post connection check

    """
    def __init__(self, factory, wrappedProtocol):
        if debug:
            print 'MyProtocolWrapper.__init__'
        ProtocolWrapper.__init__(self, factory, wrappedProtocol)

        # wrappedProtocol == client/server instance
        # factory.wrappedFactory == client/server factory

        self.data = ''
        self.encrypted = ''

        if hasattr(factory.wrappedFactory, 'getContext'):
            self.ctx = factory.wrappedFactory.getContext()
        else:
            self.ctx = Context()

        if hasattr(factory.wrappedFactory, 'sslPostConnectionCheck'):
            self.sslPostConnectionCheck = factory.wrappedFactory.sslPostConnectionCheck

        self.tlsStarted = False

        if hasattr(factory.wrappedFactory, 'startTLS'):
            if factory.wrappedFactory.startTLS:
                self.startTLS()

    def startTLS(self):
        self.internalBio = m2.bio_new(m2.bio_s_bio())
        m2.bio_set_write_buf_size(self.internalBio, 8192*8) # XXX change size
        self.networkBio = m2.bio_new(m2.bio_s_bio())
        m2.bio_set_write_buf_size(self.networkBio, 8192*8) # XXX change size
        m2.bio_make_bio_pair(self.internalBio, self.networkBio)

        self.sslBio = m2.bio_new(m2.bio_f_ssl())

        # XXX Things still don't work if we try to write more than buf at one
        # XXX time. Dunno what would help, maybe this?
        # XXX self.iossl = m2.bio_new(m2.bio_f_buffer()) ? 
        # XXX m2.bio_push(self.iossl, self,sslBio) ?

        self.ssl = m2.ssl_new(self.ctx.ctx)
        
        m2.ssl_set_connect_state(self.ssl) # XXX client only
        m2.ssl_set_bio(self.ssl, self.internalBio, self.internalBio)
        m2.bio_set_ssl(self.sslBio, self.ssl, 1)

        self.tlsStarted = True

    def makeConnection(self, transport):
        if debug:
            print 'MyProtocolWrapper.makeConnection'
        ProtocolWrapper.makeConnection(self, transport)

    def _encrypt(self, data=''):
        self.data += data
        g = m2.bio_ctrl_get_write_guarantee(self.sslBio)
        if g > 0:
            r = m2.bio_write(self.sslBio, self.data)
            if r <= 0:
                assert(m2.bio_should_retry(self.sslBio))
            else:
                self.data = self.data[r:]
        encryptedData = ''
        while 1:
            pending = m2.bio_ctrl_pending(self.networkBio)
            if pending:
                d = m2.bio_read(self.networkBio, pending)
                if d is not None: # This is strange, but seems to happen
                    encryptedData += d
            else:
                break
        return encryptedData

    def _decrypt(self, data=''):
        self.encrypted += data
        g = m2.bio_ctrl_get_write_guarantee(self.networkBio)
        if g > 0:
            r = m2.bio_write(self.networkBio, self.encrypted)
            if r <= 0:
                assert(m2.bio_should_retry(self.networkBio))
            else:
                self.encrypted = self.encrypted[r:]
        decryptedData = ''
        while 1:
            pending = m2.bio_ctrl_pending(self.sslBio)
            if pending:
                d = m2.bio_read(self.sslBio, pending)
                if d is not None: # This is strange, but seems to happen
                    decryptedData += d
            else:
                break
        return decryptedData

    def write(self, data):
        if debug:
            print 'MyProtocolWrapper.write'
        if not self.tlsStarted:
            ProtocolWrapper.write(self, data)
            return

        encryptedData = self._encrypt(data)
        ProtocolWrapper.write(self, encryptedData)

    def writeSequence(self, data):
        if debug:
            print 'MyProtocolWrapper.writeSequence'
        if not self.tlsStarted:
            ProtocolWrapper.writeSequence(self, ''.join(data))
            return

        self.write(''.join(data))

    def loseConnection(self):
        if debug:
            print 'MyProtocolWrapper.loseConnection'
        ProtocolWrapper.loseConnection(self)

    def registerProducer(self, producer, streaming):
        if debug:
            print 'MyProtocolWrapper.registerProducer'
        ProtocolWrapper.registerProducer(self, producer, streaming)

    def unregisterProducer(self):
        if debug:
            print 'MyProtocolWrapper.unregisterProducer'
        ProtocolWrapper.unregisterProducer(self)

    def stopConsuming(self):
        if debug:
            print 'MyProtocolWrapper.stopConsuming'
        ProtocolWrapper.stopConsuming(self)

    def connectionMade(self):
        if debug:
            print 'MyProtocolWrapper.connectionMade'
        ProtocolWrapper.connectionMade(self)

    def dataReceived(self, data):
        if debug:
            print 'MyProtocolWrapper.dataReceived'
        if not self.tlsStarted:
            ProtocolWrapper.dataReceived(self, data)
            return

        decryptedData = self._decrypt(data)

        if self.data or m2.bio_ctrl_pending(self.networkBio):
            encryptedData = self._encrypt()
            ProtocolWrapper.write(self, encryptedData)

        if debug:
            print 'sending decrypted off', decryptedData
            print m2.bio_ctrl_pending(self.sslBio)
            print m2.bio_ctrl_pending(self.networkBio)

        ProtocolWrapper.dataReceived(self, decryptedData)

    def connectionLost(self, reason):
        if debug and 0:
            print 'MyProtocolWrapper.connectionLost'
            print 'data', self.data
            print 'encrypted', self.encrypted
            print m2.bio_ctrl_pending(self.sslBio)
            print m2.bio_ctrl_pending(self.networkBio)

            decryptedData = self._decrypt()
            if decryptedData:
                ProtocolWrapper.dataReceived(self, decryptedData)
        
        if self.sslBio:
            m2.bio_free_all(self.sslBio)
            self.sslBio = None
        self.internalBio = None
        self.networkBio = None

        ProtocolWrapper.connectionLost(self, reason)

