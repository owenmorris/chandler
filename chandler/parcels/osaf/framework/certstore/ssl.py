"""
SSL/TLS.

@copyright: Copyright (c) 2005 Open Source Applications Foundation
@license:   http://osafoundation.org/Chandler_0.1_license_terms.htm

@var  trusted_until_shutdown_site_certs:         Certificates that should be
                                                 trusted until program exit.
                                                 The certificates are in PEM
                                                 format (str).
@type trusted_until_shutdown_site_certs:         list
@var  trusted_until_shutdown_invalid_site_certs: Ignore SSL errors with these
                                                 certificates until program
                                                 exit. The key is the
                                                 certificate in PEM format (str)
                                                 and the value is a list of the
                                                 errors to ignore.
@type trusted_until_shutdown_invalid_site_certs: dict
@var  unknown_issuer:                            Certificate verification error
                                                 codes in this list signal that
                                                 the certificate has been
                                                 issued by unknown authority
                                                 and that we should probably
                                                 ask the user if they would
                                                 like to trust this certificate.
@type unknown_issuer:                            list
"""

import logging

import wx
import M2Crypto
import M2Crypto.m2 as m2
import M2Crypto.SSL as SSL
import M2Crypto.SSL.TwistedProtocolWrapper as wrapper
import M2Crypto.SSL.Checker as Checker
import M2Crypto.X509 as X509
import twisted
import twisted.protocols.policies as policies
from i18n import OSAFMessageFactory as _

import application.Utility as Utility
from osaf.framework.certstore import constants, utils

__all__ = ['loadCertificatesToContext', 'SSLContextError', 'getContext',
           'connectSSL', 'connectTCP', 'unknown_issuer',
           'trusted_until_shutdown_site_certs',
           'trusted_until_shutdown_invalid_site_certs',
           'askTrustSiteCertificate',
           'askIgnoreSSLError']

log = logging.getLogger(__name__)

def loadCertificatesToContext(repView, ctx):
    """
    Add certificates to SSL Context.
    
    @param repView: repository view
    @param ctx:     M2Crypto.SSL.Context
    """
    qName = 'sslCertificateQuery'
    q = repView.findPath('//userdata/%s' %(qName))
    if q is None:
        from osaf.pim.collections import FilteredCollection
        from osaf.framework.certstore import certificate
        
        q = FilteredCollection(qName, itsView=repView,
                               source=utils.getExtent(certificate.Certificate,
                                                      repView),
                               filterExpression=u'item.type == "%s" and item.trust == %d' % (constants.TYPE_ROOT, constants.TRUST_AUTHENTICITY | constants.TRUST_SITE),
                               filterAttributes=['type', 'trust'])
        
    store = ctx.get_cert_store()
    for cert in q:
        store.add_x509(cert.asX509())


class SSLContextError(utils.CertificateException):
    """
    Raised when an SSL Context could not be created. Currently happens
    only when cipher list cannot be set.
    """


def getContext(repositoryView, protocol='sslv23', verify=True,
               verifyCallback=None):
    """
    Get an SSL context. You should use this method to get a context
    in Chandler rather than creating them directly.

    @param repositoryView: Repository View from which to get certificates.
    @type repositoryView:  RepositoryView
    @param protocol:       An SSL protocol version string.
    @type protocol:        str
    @param verify:         Verify SSL/TLS connection. True by default.
    @type verify:          boolean
    @param verifyCallback: Function to call for certificate verification.
    @type verifyCallback:  Callback function
    """
    ctx = SSL.Context(protocol)

    # XXX Sometimes we might want to accept any cert, and only use
    #     sslPostConnectionCheck. Need an extra arg in calling func.

    # XXX We might want to accept any cert, and store it among with info
    #     who the other user is, and if at any time in the future these
    #     don't match, alert the user (vulnerable in first connection)
    #     Need to expand API.

    if verify:
        repositoryView.refresh()
        loadCertificatesToContext(repositoryView, ctx)
        
        # XXX TODO In some cases, for example when connecting directly
        #          to P2P partner, we want to authenticate mutually using
        #          certificates so we need to load the "me" certificate.
        #          Do not do this for all contexts, however, because it can
        #          leak our identity when connecting to random SSL servers
        #          out there.
        #ctx.load_cert_chain('client.pem')

        ctx.set_verify(SSL.verify_peer | SSL.verify_fail_if_no_peer_cert,
                       9, verifyCallback)

    # Do not allow SSLv2 because it has security issues
    ctx.set_options(SSL.op_all | SSL.op_no_sslv2)

    # Disable unsafe ciphers, and order the remaining so that strongest
    # comes first, which can help peers select the strongest common
    # cipher.
    if ctx.set_cipher_list('ALL:!ADH:!LOW:!EXP:!MD5:@STRENGTH') != 1:
        log.error('Could not set cipher list')
        raise SSLContextError(_(u'Could not set cipher list'))

    return ctx


class ContextFactory(object):
    """
    This is internal class to this module and should not be used outside.
    """
    def __init__(self, repositoryView, protocol='sslv23', verify=True,
                 verifyCallback=None):
        self.repositoryView = repositoryView
        self.protocol = protocol
        self.verify = verify
        self.verifyCallback = verifyCallback

    def getContext(self):
        return getContext(self.repositoryView, self.protocol, self.verify,
                          self.verifyCallback)

trusted_until_shutdown_site_certs = []
trusted_until_shutdown_invalid_site_certs = {}

# There are (at least) these errors that will happen when
# the certificate can't be verified because we don't have
# the issuing certificate.
unknown_issuer = [m2.X509_V_ERR_DEPTH_ZERO_SELF_SIGNED_CERT,
                  m2.X509_V_ERR_UNABLE_TO_GET_ISSUER_CERT_LOCALLY,
                  m2.X509_V_ERR_CERT_UNTRUSTED,
                  m2.X509_V_ERR_UNABLE_TO_VERIFY_LEAF_SIGNATURE]


class TwistedProtocolWrapper(wrapper.TLSProtocolWrapper):
    """
    This is internal class to this module and should not be used outside.
    """
    def __init__(self, repositoryView, protocol, factory, wrappedProtocol, 
                 startPassThrough, client):
        log.debug('TwistedProtocolWrapper.__init__')
        self.contextFactory = ContextFactory(repositoryView, protocol, 
                                            verifyCallback=self.verifyCallback)
        wrapper.TLSProtocolWrapper.__init__(self, factory, wrappedProtocol, 
                                            startPassThrough, client,
                                            self.contextFactory,
                                            self.postConnectionVerify)
        self.repositoryView = repositoryView
        # List for now, even though only first might be needed:
        self.untrustedCertificates = []

    def verifyCallback(self, ok, store):
        log.debug('TwistedProtocolWrapper.verifyCallback')
        global trusted_until_shutdown_site_certs, \
               trusted_until_shutdown_invalid_site_certs, \
               unknown_issuer
                        
        if not ok:
            err = store.get_error()

            x509 = store.get_current_cert()

            # Check temporarily trusted certificates
            pem = x509.as_pem()

            if err not in unknown_issuer:
                # Check if we are temporarily ignoring errors with this cert
                acceptedErrList = trusted_until_shutdown_invalid_site_certs.get(pem)
                if acceptedErrList is not None and err in acceptedErrList:
                    log.debug('Ignoring certificate error %d' %err)
                    return 1
                self.untrustedCertificates.append(pem)
                return ok

            if pem in trusted_until_shutdown_site_certs:
                log.debug('Found temporarily trusted site cert')
                return 1

            # Check permanently trusted certificates
            # XXX Why does this need to be commit()? refresh() does not
            # XXX seem pick up changes made in main thread.
            self.repositoryView.commit()

            q = self.repositoryView.findPath('//userdata/%s' %(constants.TRUSTED_SITE_CERTS_QUERY_NAME))
            if q is not None:
                for cert in q:
                    if cert.pemAsString() == pem:
                        log.debug('Found permanently trusted site cert')
                        return 1

            self.untrustedCertificates.append(pem)

        log.debug('Returning %d' % ok)
        return ok

    def dataReceived(self, data):
        log.debug('TwistedProtocolWrapper.dataReceived')
        utils.entropyInitialized = True
        try:
            wrapper.TLSProtocolWrapper.dataReceived(self, data)
        except M2Crypto.BIO.BIOError, e:
            if e.args[1] == 'certificate verify failed':
                raise Utility.CertificateVerificationError(e.args[0], e.args[1],
                                                   self.untrustedCertificates)
            raise


    def postConnectionVerify(self, peerX509, expectedHost):
        #Do a post connection check on an SSL connection. This is done just
        #after the SSL connection has been established, but before exchanging
        #any real application data like username and password.
        #
        #This implementation checks to make sure that the certificate that the
        #peer presented was issued for the host we tried to connect to, or in
        #other words, make sure that we are talking to the server we think we
        #should be talking to.
        #
        # TODO: We should report ALL errors from this post connection check
        #       so that users will only get one dialog, even if there are
        #       several errors. Obviously we need to record all errors in
        #       verifyCallback first.
        check = Checker.Checker()
        try:
            return check(peerX509, expectedHost)
        except Checker.WrongHost, e:
            e.pem = peerX509.as_pem()
    
            acceptedErrList = trusted_until_shutdown_invalid_site_certs.get(e.pem)
            if acceptedErrList is not None and str(e) in acceptedErrList:
                log.debug('Ignoring post connection error %s' %str(e))
                return 1
    
            raise e


def connectSSL(host, port, factory, repositoryView, 
               protocol='sslv23',
               timeout=30,
               bindAddress=None,
               reactor=twisted.internet.reactor):
    """
    A convenience function to start an SSL/TLS connection using Twisted.
    
    See IReactorSSL interface in Twisted. 
    """
    log.debug('connectSSL(host=%s, port=%d)' %(host, port))
    wrappingFactory = policies.WrappingFactory(factory)
    wrappingFactory.protocol = lambda factory, wrappedProtocol: \
        TwistedProtocolWrapper(repositoryView,
                               protocol,
                               factory,
                               wrappedProtocol,
                               startPassThrough=0,
                               client=1)
    return reactor.connectTCP(host, port, wrappingFactory, timeout,
                              bindAddress)
    

def connectTCP(host, port, factory, repositoryView, 
               protocol='tlsv1',
               timeout=30,
               bindAddress=None,
               reactor=twisted.internet.reactor):
    """
    A convenience function to start a TCP connection using Twisted.
    
    NOTE: You must call startTLS(ctx) to go into SSL/TLS mode.
    
    See IReactorSSL interface in Twisted. 
    """
    log.debug('connectTCP(host=%s, port=%d)' %(host, port))
    wrappingFactory = policies.WrappingFactory(factory)
    wrappingFactory.protocol = lambda factory, wrappedProtocol: \
        TwistedProtocolWrapper(repositoryView,
                               protocol,
                               factory,
                               wrappedProtocol,
                               startPassThrough=1,
                               client=1)
    return reactor.connectTCP(host, port, wrappingFactory, timeout,
                              bindAddress)    

def askTrustSiteCertificate(repositoryView, pem, reconnect):
    """
    Ask user if they would like to trust the certificate that was returned by
    the server. This will only happen if the certificate is not already
    trusted, either by trust chain or explicitly.
    
    @param repositoryView: Should be the main view.
    @param pem:            The certificate in PEM format.
    @param reconnect:      The reconnect callback that will be called if the
                           used chooses to trust the certificate.
    """
    from osaf.framework.certstore import dialogs, certificate
    global trusted_until_shutdown_site_certs, \
           trusted_until_shutdown_invalid_site_certs, \
           unknown_issuer
    x509 = X509.load_cert_string(pem)
    untrustedCertificate = certificate.findCertificate(repositoryView, pem)
    dlg = dialogs.TrustSiteCertificateDialog(wx.GetApp().mainFrame,
                                             x509,
                                             untrustedCertificate)
    try:
        if dlg.ShowModal() == wx.ID_OK:
            selection = dlg.GetSelection()

            if selection == 0:
                trusted_until_shutdown_site_certs += [pem]
            else:
                if untrustedCertificate is not None:
                    untrustedCertificate.trust |= constants.TRUST_AUTHENTICITY
                else:
                    fingerprint = utils.fingerprint(x509)
                    certificate.importCertificate(x509, fingerprint, 
                                                  constants.TRUST_AUTHENTICITY,
                                                  repositoryView)

            reconnect()
    finally:
        dlg.Destroy()

def askIgnoreSSLError(pem, err, reconnect):
    """
    Ask user if they would like to ignore an error with the SSL connection,
    and if so, reconnect automatically.
    
    Strictly speaking we should not ask and just fail. In practice that
    wouldn't be very helpful because there are lots of misconfigured servers
    out there.
    
    @param pem:       The certificate with which we noticed the error (the
                      error could be in the certificate itself, or it could be
                      a mismatch between the certificate and the server).
    @param err:       Error.
    @param reconnect: The reconnect callback that will be called if the used
                      chooses to ignore the error.
    """
    from osaf.framework.certstore import dialogs
    global trusted_until_shutdown_site_certs, \
           trusted_until_shutdown_invalid_site_certs, \
           unknown_issuer
    x509 = X509.load_cert_string(pem)
    dlg = dialogs.IgnoreSSLErrorDialog(wx.GetApp().mainFrame,
                                       x509,
                                       err)
    try:
        if dlg.ShowModal() == wx.ID_OK:
            acceptedErrList = trusted_until_shutdown_invalid_site_certs.get(pem)
            if acceptedErrList is None:
                trusted_until_shutdown_invalid_site_certs[pem] = [err]
            else:
                trusted_until_shutdown_invalid_site_certs[pem].append(err)
            reconnect()
    finally:
        dlg.Destroy()

