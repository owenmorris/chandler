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

    def __del__(self):
        self.clear()

    def clear(self):
        if self.tlsStarted:
            if self.sslBio:
                m2.bio_free_all(self.sslBio)
            self.sslBio = None
            self.internalBio = None
            self.networkBio = None
        self.data = ''
        self.encrypted = ''
        # We can reuse self.ctx and it will be deleted automatically
        # when this instance dies
        
    def startTLS(self):
        if self.tlsStarted:
            raise Exception, 'TLS already started'
        
        self.internalBio = m2.bio_new(m2.bio_s_bio())
        m2.bio_set_write_buf_size(self.internalBio, 0)
        self.networkBio = m2.bio_new(m2.bio_s_bio())
        m2.bio_set_write_buf_size(self.networkBio, 0)
        m2.bio_make_bio_pair(self.internalBio, self.networkBio)

        self.sslBio = m2.bio_new(m2.bio_f_ssl())

        self.ssl = m2.ssl_new(self.ctx.ctx)
        
        m2.ssl_set_connect_state(self.ssl) # XXX client only
        m2.ssl_set_bio(self.ssl, self.internalBio, self.internalBio)
        m2.bio_set_ssl(self.sslBio, self.ssl, 1)

        # Need this for writes that are larger than BIO pair buffers
        mode = m2.ssl_get_mode(self.ssl)
        m2.ssl_set_mode(self.ssl,
                        mode |
                        m2.SSL_MODE_ENABLE_PARTIAL_WRITE |
                        m2.SSL_MODE_ACCEPT_MOVING_WRITE_BUFFER)

        self.tlsStarted = True

    def makeConnection(self, transport):
        if debug:
            print 'MyProtocolWrapper.makeConnection'
        ProtocolWrapper.makeConnection(self, transport)

    def _encrypt(self, data=''):
        # XXX mirror image of _decrypt - refactor
        self.data += data
        encryptedData = ''
        g = m2.bio_ctrl_get_write_guarantee(self.sslBio)
        if g > 0 and self.data != '':
            r = m2.bio_write(self.sslBio, self.data)
            if r <= 0:
                assert(m2.bio_should_retry(self.sslBio))
            else:
                self.data = self.data[r:]
                
        while 1:
            pending = m2.bio_ctrl_pending(self.networkBio)
            if pending:
                d = m2.bio_read(self.networkBio, pending)
                if d is not None: # This is strange, but d can be None
                    encryptedData += d
                else:
                    assert(m2.bio_should_retry(self.networkBio))
            else:
                break
        return encryptedData

    def _decrypt(self, data=''):
        # XXX mirror image of _encrypt - refactor
        self.encrypted += data
        decryptedData = ''
        g = m2.bio_ctrl_get_write_guarantee(self.networkBio)
        if g > 0 and self.encrypted != '':
            r = m2.bio_write(self.networkBio, self.encrypted)
            if r <= 0:
                assert(m2.bio_should_retry(self.networkBio))
            else:
                self.encrypted = self.encrypted[r:]
                
        while 1:
            pending = m2.bio_ctrl_pending(self.sslBio)
            if pending:
                d = m2.bio_read(self.sslBio, pending)
                if d is not None: # This is strange, but d can be None
                    decryptedData += d
                else:
                    assert(m2.bio_should_retry(self.sslBio))
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
            # XXX STARTTLS support
            ProtocolWrapper.dataReceived(self, data)
            return

        decryptedData = '1'
        encryptedData = '1'
        self.encrypted += data
        while decryptedData != '' or encryptedData != '':

            if debug:
                print 'before:', len(encryptedData), len(self.data), m2.bio_ctrl_pending(self.networkBio), len(decryptedData), len(self.encrypted)

            decryptedData = self._decrypt()

            encryptedData = self._encrypt()
            ProtocolWrapper.write(self, encryptedData)

            ProtocolWrapper.dataReceived(self, decryptedData)

    def connectionLost(self, reason):
        if debug:
            print 'MyProtocolWrapper.connectionLost'
        self.clear()

        ProtocolWrapper.connectionLost(self, reason)

