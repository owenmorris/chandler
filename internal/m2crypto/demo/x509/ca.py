#!/usr/bin/env python

"""
How to create a CA certificate with Python.

WARNING: This sample only demonstrates how to use the objects and methods,
         not how to create a safe and correct certificate.

Copyright (c) 2004 Open Source Applications Foundation.
Author: Heikki Toivonen
"""

from M2Crypto import RSA, X509, EVP, m2

### key
# XXX Need to initialize rand
# XXX Do I actually need more keys?
key = RSA.gen_key(2048, m2.RSA_F4)

### request
req = X509.Request()
pkey = EVP.PKey()
pkey.assign_rsa(key)
req.set_version(0)# Seems to default to 0, but we can now set it as well
req.set_pubkey(pkey)
# XXX Need to set subjectName
req.sign(pkey, 'sha1')

print req.as_text()

### Certificate
#req.verify(pkey)
cert = X509.X509()
cert.set_version(2)
# XXX Set subjectName
# XXX Set issuerName
cert.set_pubkey(pkey)
notBefore = m2.x509_get_not_before(cert.x509)
notAfter  = m2.x509_get_not_after(cert.x509)
m2.x509_gmtime_adj(notBefore, 0)
days = 30
m2.x509_gmtime_adj(notAfter, 60*60*24*days)

# XXX extensions

cert.sign(pkey, 'sha1')

print cert.as_text()
