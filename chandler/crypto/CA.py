"""
A primitive CA.
"""

__copyright__ = "Copyright (c) 2004 Open Source Applications Foundation"
__license__   = "http://osafoundation.org/Chandler_0.1_license_terms.htm"

from M2Crypto import RSA, X509, EVP, m2, Rand, Err

# XXX Check return values from functions

def _keygen_callback(self, p, n, out):
    # XXX Provide progress feedback in UI, see M2Crypto.RSA
    pass

def generateRSAKey():
    return RSA.gen_key(2048, m2.RSA_F4, callback=_keygen_callback)

def makePKey(rsa):
    pkey = EVP.PKey()
    pkey.assign_rsa(rsa)
    return pkey
    
def makeRequest(pkey):
    req = X509.Request()
    req.set_pubkey(pkey)
    name = X509.X509_Name()
    name.CN = 'Chandler'
    req.set_subject(name)
    req.sign(pkey, 'sha1')
    return req

def makeCert(req, caPkey, availableSerialNumber):
    pkey = req.get_pubkey()
    if not req.verify(pkey):
        raise Exception, 'Error verifying request'
    sub = req.get_subject()
    cert = X509.X509()
    cert.set_serial_number(availableSerialNumber)
    cert.set_version(2)
    cert.set_subject(sub)
    issuer = X509.X509_Name()
    issuer.CN = 'Chandler CA'
    cert.set_issuer(issuer)
    cert.set_pubkey(EVP.PKey(pkey))

    # XXX There should be an easy method on X509 to set this
    # XXX gmtime is also not your local time, most likely
    notBefore = m2.x509_get_not_before(cert.x509)
    notAfter  = m2.x509_get_not_after(cert.x509)
    m2.x509_gmtime_adj(notBefore, 0)
    days = 180
    m2.x509_gmtime_adj(notAfter, 60*60*24*days)

    cert.add_ext(
        X509.X509_Extension('basicConstraints', 'CA:TRUE'))
    ext = X509.X509_Extension('nsComment', 'Chandler CA Certificate')
    cert.add_ext(ext)
    cert.sign(caPkey, 'sha1')
    return cert

def ca(availableSerialNumber):
    rsa = generateRSAKey()
    pkey = makePKey(rsa)
    req = makeRequest(pkey)
    cert = makeCert(req, pkey, availableSerialNumber)
    return (cert, pkey, rsa) # XXX Shouldn't need to return pkey, see bug 1542
