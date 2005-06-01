"""
SSL/TLS-related functionality.

@copyright: Copyright (c) 2004-2005 Open Source Applications Foundation
@license:   http://osafoundation.org/Chandler_0.1_license_terms.htm
"""

from M2Crypto import SSL, util, EVP, httpslib
import M2Crypto.SSL.Checker as Checker
import M2Crypto.m2 as m2

class SSLVerificationError(Exception):
    pass

class NoCertificate(SSLVerificationError):
    pass

class WrongCertificate(SSLVerificationError):
    pass

class WrongHost(SSLVerificationError):
    pass

class SSLContextError(Exception):
    pass


def postConnectionCheck(peerX509, expectedHost):
    """
    Do a post connection check on an SSL connection. This is done just
    after the SSL connection has been established, but before exchanging
    any real application data like username and password.

    This implementation checks to make sure that the certificate that the
    peer presented was issued for the host we tried to connect to, or in
    other words, make sure that we are talking to the server we think we should
    be talking to.
    """
    check = Checker.Checker()
    # XXX This may raise exceptions about wrong host. Sometimes this is due
    # XXX to server misconfiguration rather than an active attack. We should
    # XXX really ask the user what they want to do. This is bug 3156.
    return check(peerX509, expectedHost)


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
                           If nothing is specified, a default is used.
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
        # XXX Now we depend on parcels
        import osaf.framework.certstore.ssl as ssl

        repositoryView.refresh()
        ssl.addCertificates(repositoryView, ctx)
        
        # XXX TODO In some cases, for example when connecting directly
        #          to P2P partner, we want to authenticate mutually using
        #          certificates so we need to load the "me" certificate.
        #          Do not do this for all contexts, however, because it can
        #          leak our identity when connecting to random SSL servers
        #          out there.
        #ctx.load_cert_chain('client.pem')

        if not verifyCallback:
            verifyCallback = _VerifyCallback(repositoryView)

        ctx.set_verify(SSL.verify_peer | SSL.verify_fail_if_no_peer_cert,
                       9)#, verifyCallback) #XXX callback causes crash

    # Do not allow SSLv2 because it has security issues
    ctx.set_options(SSL.op_all | SSL.op_no_sslv2)

    # Disable unsafe ciphers, and order the remaining so that strongest
    # comes first, which can help peers select the strongest common
    # cipher.
    if ctx.set_cipher_list('ALL:!ADH:!LOW:!EXP:!MD5:@STRENGTH') != 1:
        raise SSLContextError, 'Could not set cipher list'

    return ctx


class _VerifyCallback(object):
    # We need to use a class to transmit the repository view. Otherwise
    # this could be an ordinary function instead of a class with __call__.
    
    trusted_until_shutdown_site_certs = []

    def __init__(self, repositoryView):
        self.repositoryView = repositoryView

    def __call__(ok, store):
        if not ok:
            err = store.get_error()

            # There are (at least) these errors that will happen when
            # the certificate can't be verified because we don't have
            # the issuing certificate.
            # We are being conservative for now and failing validation if the
            # error code is something else - this may need to be tweaked.
            if err != m2.X509_V_ERR_UNABLE_TO_GET_ISSUER_CERT_LOCALLY and \
               err != m2.X509_V_ERR_CERT_UNTRUSTED and \
               err != m2.X509_V_ERR_UNABLE_TO_VERIFY_LEAF_SIGNATURE:
                return ok

            x509 = store.get_current_cert()

            pem = x509.as_pem()
            if pem in trusted_until_shutdown_site_certs:
                return 1

            # XXX Need to see if certificate is permanently trusted and
            # XXX stored in the repository.
            # XXX For this we need self.repositoryView

            # XXX Need to put up a dialog for the user where they
            # XXX can decide what they want to do. This may in fact need
            # XXX to live elsewhere - where we currently put up the connection
            # XXX failure error for example.

        return ok


class HTTPSConnection(httpslib.HTTPSConnection):
    def connect(self):
        httpslib.HTTPSConnection.connect(self)
        postConnectionCheck(self.sock.get_peer_cert(), self.sock.addr[0])
