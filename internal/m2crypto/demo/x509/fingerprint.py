#!/usr/bin/env python

"""
How to create the fingerprint of a certificate with Python.

Copyright (c) 2004 Open Source Applications Foundation.
Author: Heikki Toivonen
"""

import os
from M2Crypto import X509, util
from M2Crypto.EVP import MessageDigest

def test():
    cmd = os.popen('openssl x509 -fingerprint -sha1 -noout -in server.pem')
    expected = cmd.read()
    expected = expected[expected.find('=')+1:].strip()

    cert = X509.load_cert('server.pem')
    der = cert.as_der()
    md = MessageDigest('sha1')
    md.update(der)
    digest = md.final()
    
    hexstr = hex(util.octx_to_num(digest))
    fingerprint = hexstr[2:len(hexstr)-1]
    list = [fingerprint[x:x+2] for x in range(len(fingerprint)) if x%2 == 0]
    fingerprint = ':'.join(list)
    
    if expected == fingerprint:
        print "Fingerprint matched"
    else:
        print "Unexpected fingerprint"
        print "Expected: ", expected
        print "Got:      ", fingerprint

if __name__ == "__main__":
    test()
