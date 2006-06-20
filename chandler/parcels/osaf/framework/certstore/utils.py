#   Copyright (c) 2005-2006 Open Source Applications Foundation
#
#   Licensed under the Apache License, Version 2.0 (the "License");
#   you may not use this file except in compliance with the License.
#   You may obtain a copy of the License at
#
#       http://www.apache.org/licenses/LICENSE-2.0
#
#   Unless required by applicable law or agreed to in writing, software
#   distributed under the License is distributed on an "AS IS" BASIS,
#   WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
#   See the License for the specific language governing permissions and
#   limitations under the License.


"""
Certificate utilities.

@var entropyInitialized: If this is true, then some crypto operation
                         has needed to use entropy, and it is likely
                         there will be more. At least the initialization
                         (which can be slow) has happened.
"""

import M2Crypto.EVP as EVP
import M2Crypto.util as util

from application import schema
from osaf import ChandlerException

__all__ = ['CertificateException', 'fingerprint', 'getExtent', 
           'entropyInitialized']
            
class CertificateException(ChandlerException):
    pass

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
        name = 'exactExtent'
    else:
        name = 'fullExtent'

    return kind[name]

# Make sure to set this to true if any operation initializes entropy.
# For example, after creating random path names or starting an SSL connection.
entropyInitialized = False
