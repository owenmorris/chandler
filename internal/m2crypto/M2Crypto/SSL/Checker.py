class SSLVerificationError(Exception):
    pass

class NoCertificate(SSLVerificationError):
    pass

class WrongCertificate(SSLVerificationError):
    pass

class WrongHost(SSLVerificationError):
    pass

class Checker:
    def __init__(self, host=None, peerCertHash=None, peerCertDigest='sha1'):
        self.host = host
        self.fingerprint = peerCertHash
        self.digest = peerCertDigest

    def __call__(self, peerCert):
        if peerCert is None:
            raise NoCertificate, 'peer did not return certificate'
        
        if self.fingerprint:
            der = peerCert.as_der()
            md = EVP.MessageDigest(self.digest)
            md.update(der)
            digest = md.final() # XXX See if we can compare as numbers
            hexstr = hex(util.octx_to_num(digest))
            fingerprint = hexstr[2:len(hexstr)-1]
            fpLen = len(fingerprint)
            if fpLen < 40: # len(sha1 in hex) == 40
                fingerprint = '0' * (40 - fpLen) + fingerprint # Pad with 0's
            if fingerprint != certSha1Fingerprint:
                raise WrongCertificate, 'peer certificate fingerprint does not match'

        if host:
            hostValidationPassed = False

            # XXX See RFC 2818 (and maybe 3280) for matching rules

            # XXX subjectAltName might contain multiple fields
            # subjectAltName=DNS:somehost
            try:
                if cert.get_ext('subjectAltName').get_value() != 'DNS:' + host:
                    raise SSLError, 'subjectAltName does not match host'
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

