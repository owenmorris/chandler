"""
Cryptographic services.

@copyright = Copyright (c) 2004 Open Source Applications Foundation
@license   = http://osafoundation.org/Chandler_0.1_license_terms.htm
"""

import logging
from M2Crypto import Rand, threading, SSL, util, EVP

class SSLVerificationError(Exception):
    pass

class NoCertificate(SSLVerificationError):
    pass

class WrongCertificate(SSLVerificationError):
    pass

class SSLContextError(Exception):
    pass

class Crypto(object):
    """
    Crypto services.
    """
    def __init__(self):
        self._randpool = 'randpool.dat'

    def init(self):
        """
        The crypto services must be initialized before they can be used.
        """
        self._log = logging.getLogger('crypto')
        self._log.setLevel(logging.INFO)
        self._log.info('Starting crypto services')
    
        threading.init()
        # Generating entropy can be slow, so we should try to bootstrap
        # with something.
        Rand.load_file(self._randpool, -1)

    def shutdown(self):
        """
        The crypto services must be shut down to clean things properly.
        You must reinitialize before using the crypto services again.
        """
        self._log.info('Stopping crypto services')

        # XXX Check return value and log if we failed to write data
        Rand.save_file(self._randpool)
        threading.cleanup()

    def getSSLContext(self, protocol='tlsv1', verifyCallback=None):
        """
        Get an SSL context. You should use this method to get a context
        in Chandler rather than creating them directly.

        @param protocol:       An SSL protocol version string, one of the
                               following: 'tlsv1', 'sslv3'
        @type protocol:        str
        @param verifyCallback: Function to call for certificate verification.
                               If nothing is specified, a default is used.
        @type verifyCallback:  Callback function
        """
        return self._newSSLContext(protocol, verifyCallback)

    def sslPostConnectionCheck(self, connection, certSha1Fingerprint=None,
                               host=None):
        """
        After having established an SSL connection, but before exchanging
        any data or login information, call this function
        for a final SSL check. If things don't check up, this will raise
        various SSLVerificationErrors.

        @param certSha1Fingerprint: If this is specified, the certificate
                                    returned by peer must have this SHA1
                                    fingerprint. Typically you would do this
                                    check in case where you don't check
                                    certificate chain and don't care about
                                    peer host.
        @type certSha1Fingerprint:  str
        @param host:                If this is specified, the host name
                                    specified in the peer certificate must
                                    match. This would typically be done
                                    against public servers, together with
                                    certificate chain validation.
        @type host:                 str
        """
        cert = connection.get_peer_cert()
        if cert is None:
            raise NoCertificate
        
        if certSha1Fingerprint:
            der = cert.as_der()
            md = EVP.MessageDigest('sha1')
            md.update(der)
            digest = md.final()
            hexstr = hex(util.octx_to_num(digest))
            fingerprint = hexstr[2:len(hexstr)-1]
            if fingerprint != certSha1Fingerprint:
                raise WrongCertificate

        if host:
            raise NotImplemented

    def _verifyCallback(ok, store):
        if not ok:
            raise SSLVerificationError # XXX Or should I do something else?
        return ok
        
    def _newSSLContext(self, protocol, verifyCallback):
        ctx = SSL.Context(protocol)

        # XXX check return values

        # XXX How do we do this when we store certs in the repository?

        # XXX Sometimes we might want to accept any cert, and only use
        #     sslPostConnectionCheck. Need an extra arg in calling func.

        # XXX We might want to accept any cert, and store it among with info
        #     who the other user is, and if at any time in the future these
        #     don't match, alert the user (vulnerable in first connection)
        #     Need to expand API.

        #if ctx.load_verify_locations('ca.pem') != 1:
        #    print "***No CA file"
        #if ctx.set_default_verify_paths() != 1:
        #    print "***No default verify paths"
        #ctx.load_cert_chain('client.pem')

        if not verifyCallback:
            verifyCallback = self._verifyCallback

        # XXX crash
        #ctx.set_verify(SSL.verify_peer | SSL.verify_fail_if_no_peer_cert,
        #               10, verifyCallback)

        # Do not allow SSLv2 because it has security issues
        ctx.set_options(SSL.op_all | SSL.op_no_sslv2)

        # Disable unsafe ciphers, and order the remaining so that strongest
        # comes first, which can help peers select the strongest common
        # cipher.
        if ctx.set_cipher_list('ALL:!ADH:!LOW:!EXP:!MD5:@STRENGTH') != 1:
            raise SSLContextError

        return ctx
