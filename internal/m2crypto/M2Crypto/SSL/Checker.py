from M2Crypto import util, EVP

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
            digest = md.final()
            if util.octx_to_num(digest) != int(self.fingerprint, 16):
                raise WrongCertificate, 'peer certificate fingerprint does not match'

        if self.host:
            hostValidationPassed = False

            # XXX See RFC 2818 (and maybe 3280) for matching rules

            # XXX subjectAltName might contain multiple fields
            # subjectAltName=DNS:somehost
            try:
                if peerCert.get_ext('subjectAltName').get_value() != 'DNS:' + self.host:
                    raise WrongHost, 'subjectAltName does not match host'
                hostValidationPassed = True
            except LookupError:
                pass

            # commonName=somehost
            if not hostValidationPassed:
                try:
                    if peerCert.get_subject().CN != self.host:
                        raise WrongHost, 'peer certificate commonName does not match host'
                except AttributeError:
                    raise WrongHost, 'no commonName in peer certificate'

        return True
