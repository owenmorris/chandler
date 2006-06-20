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
Error codes
"""

import M2Crypto.m2 as m2

from i18n import OSAFMessageFactory as _

certificateVerifyError = {
    m2.X509_V_ERR_UNABLE_TO_GET_ISSUER_CERT: _(u"unable to get issuer certificate"),
    m2.X509_V_ERR_UNABLE_TO_DECRYPT_CERT_SIGNATURE: _(u"unable to decrypt certificate's signature"),
    m2.X509_V_ERR_UNABLE_TO_DECODE_ISSUER_PUBLIC_KEY: _(u"unable to decode issuer public key"),
    m2.X509_V_ERR_CERT_SIGNATURE_FAILURE: _(u"certificate signature failure"),
    m2.X509_V_ERR_CERT_NOT_YET_VALID: _(u"certificate is not yet valid"),
    m2.X509_V_ERR_CERT_HAS_EXPIRED: _(u"certificate has expired"),
    m2.X509_V_ERR_ERROR_IN_CERT_NOT_BEFORE_FIELD: _(u"format error in certificate's notBefore field"),
    m2.X509_V_ERR_ERROR_IN_CERT_NOT_AFTER_FIELD: _(u"format error in certificate's notAfter field"),
    m2.X509_V_ERR_OUT_OF_MEM: _(u"out of memory"),
    m2.X509_V_ERR_DEPTH_ZERO_SELF_SIGNED_CERT: _(u"self signed certificate"),
    m2.X509_V_ERR_SELF_SIGNED_CERT_IN_CHAIN: _(u"self signed certificate in certificate chain"),
    m2.X509_V_ERR_UNABLE_TO_GET_ISSUER_CERT_LOCALLY: _(u"unable to get local issuer certificate"),
    m2.X509_V_ERR_UNABLE_TO_VERIFY_LEAF_SIGNATURE: _(u"unable to verify the first certificate"),
    m2.X509_V_ERR_INVALID_CA: _(u"invalid CA certificate"),
    m2.X509_V_ERR_PATH_LENGTH_EXCEEDED: _(u"path length constraint exceeded"),
    m2.X509_V_ERR_INVALID_PURPOSE: _(u"unsupported certificate purpose"),
    m2.X509_V_ERR_CERT_UNTRUSTED: _(u"certificate not trusted"),
    m2.X509_V_ERR_CERT_REJECTED: _(u"certificate rejected")
}

def getCertificateVerifyErrorString(code):
    """
    The the certificate verification/validation error string using the error code.
    """
    return certificateVerifyError.get(code, "%d" % code)

if __name__ == '__main__':
    assert getCertificateVerifyErrorString(m2.X509_V_ERR_UNABLE_TO_GET_ISSUER_CERT) == _(u"unable to get issuer certificate")
    assert getCertificateVerifyErrorString(m2.X509_V_OK) == "0"
