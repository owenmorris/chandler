"""
Certificate utilities.

@copyright: Copyright (c) 2005 Open Source Applications Foundation
@license:   http://osafoundation.org/Chandler_0.1_license_terms.htm
"""

import M2Crypto.EVP as EVP
import M2Crypto.util as util

from application import schema

def fingerprint(x509, md='sha1'):
    """
    Return the fingerprint of the X509 certificate.
    
    @param x509: X509 object.
    @type x509:  M2Crypto.X509.X509
    @param md:   The message digest algorithm.
    @type md:    str
    """
    der = x509.as_der()
    md = EVP.MessageDigest(md)
    md.update(der)
    digest = md.final()
    return hex(util.octx_to_num(digest))

def getExtent(cls, view=None, exact=False):
    kind = schema.itemFor(cls, view)
    # XXX Should get the names from some shared source because they are used
    # XXX in data.py as well.
    if exact:
        name = '%sCollection' % kind.itsName
    else:
        name = 'Recursive%sCollection' % kind.itsName

    return kind.findPath("//userdata/%s" % name)
