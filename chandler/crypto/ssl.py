"""
SSL/TLS-related functionality.

@copyright = Copyright (c) 2004 Open Source Applications Foundation
@license   = http://osafoundation.org/Chandler_0.1_license_terms.htm
"""

import os
from M2Crypto import SSL, util, EVP
import application.Globals 

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

class ClientContextFactory:
    """A context factory for SSL clients."""

    isClient = 1
    useM2    = 1
    method   = 'sslv23' # slv23 actually means any version of SSL

    def __init__(self, method='sslv23', verify=True):
        self.method = method
        self.verify = verify

    def getContext(self):
        return getSSLContext(protocol=self.method, verify=self.verify)


def getSSLContext(protocol='sslv23', verify=True, verifyCallback=None):
    """
    Get an SSL context. You should use this method to get a context
    in Chandler rather than creating them directly.

    @param protocol:       An SSL protocol version string.
    @type protocol:        str
    @param verify:         Verify SSL/TLS connection. True by default.
    @type verify:          boolean
    @param verifyCallback: Function to call for certificate verification.
                           If nothing is specified, a default is used.
    @type verifyCallback:  Callback function
    """
    ctx = SSL.Context(protocol)

    # XXX How do we do this when we store certs in the repository?

    # XXX Sometimes we might want to accept any cert, and only use
    #     sslPostConnectionCheck. Need an extra arg in calling func.

    # XXX We might want to accept any cert, and store it among with info
    #     who the other user is, and if at any time in the future these
    #     don't match, alert the user (vulnerable in first connection)
    #     Need to expand API.

    if verify:
        # XXX We'd like to load the CA certs from repository, or better yet,
        # XXX provide BIO 'directory' from which to load certs on demand.
        parcelDir = os.getenv('PARCELDIR')
        caCertFile = None
        if parcelDir is not None:
            caCertFile = os.path.join(parcelDir, 'personal', 'cacert.pem')
            if not os.path.exists(caCertFile):
                caCertFile = None
        if caCertFile is None:
            caCertFile = os.path.join(application.Globals.options.profileDir, 'cacert.pem')
        if ctx.load_verify_locations(caCertFile) != 1:
            raise SSLContextError, "No CA certificate file"

        # XXX TODO In some cases, for example when connecting directly
        #          to P2P partner, we want to authenticate mutually using
        #          certificates so we need to load the "me" certificate.
        #          Do not do this for all contexts, however, because it can
        #          leak our identity when connecting to random SSL servers
        #          out there.
        #ctx.load_cert_chain('client.pem')

        if not verifyCallback:
            verifyCallback = _verifyCallback

        # XXX crash with callback
        ctx.set_verify(SSL.verify_peer | SSL.verify_fail_if_no_peer_cert,
                       9)#, verifyCallback)

    # Do not allow SSLv2 because it has security issues
    ctx.set_options(SSL.op_all | SSL.op_no_sslv2)

    # Disable unsafe ciphers, and order the remaining so that strongest
    # comes first, which can help peers select the strongest common
    # cipher.
    if ctx.set_cipher_list('ALL:!ADH:!LOW:!EXP:!MD5:@STRENGTH') != 1:
        raise SSLContextError, 'Could not set cipher list'

    return ctx


def postConnectionCheck(connection, certSha1Fingerprint=None,
                        hostCheck=True):
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
    @param hostCheck:           If this is True, the host name
                                specified in the peer certificate must
                                match connected peer. This would typically
                                be done against public servers, together with
                                certificate chain validation.
    @type hostCheck:            boolean
    """
    cert = connection.get_peer_cert()
    if cert is None:
        raise NoCertificate, 'peer did not return certificate'

    if certSha1Fingerprint:
        der = cert.as_der()
        md = EVP.MessageDigest('sha1')
        md.update(der)
        digest = md.final() # XXX See if we can compare as numbers
        hexstr = hex(util.octx_to_num(digest))
        fingerprint = hexstr[2:len(hexstr)-1]
        fpLen = len(fingerprint)
        if fpLen < 40: # len(sha1 in hex) == 40
            fingerprint = '0' * (40 - fpLen) + fingerprint # Pad with 0's
        if fingerprint != certSha1Fingerprint:
            raise WrongCertificate, 'peer certificate fingerprint does not match'

    if hostCheck:
        hostValidationPassed = False

        # XXX Is there any possibility that we would like to pass in a
        # XXX different host and compare against it? Is connection.addr
        # XXX what we set it in the beginning, or is it whatever we are
        # XXX connected to at the moment (in which case this would be
        # XXX a security hole)?
        host = connection.addr[0]

        # XXX See RFC 2818 (and maybe 3280) for matching rules

        # XXX subjectAltName might contain multiple fields
        # subjectAltName=DNS:somehost
        try:
            if cert.get_ext('subjectAltName').get_value() != 'DNS:' + host:
                raise WrongHost, 'subjectAltName does not match host'
            hostValidationPassed = True
        except LookupError:
            pass

        # commonName=somehost
        if not hostValidationPassed:
            try:
                if cert.get_subject().CN != host:
                    raise WrongHost, 'peer certificate commonName does not match host'
            except AttributeError:
                raise WrongHost, 'no commonName in peer certificate'


def _verifyCallback(ok, store):
    if not ok:
        raise SSLVerificationError # XXX Or should I do something else?
    return ok
