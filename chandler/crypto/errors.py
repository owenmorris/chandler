"""
Error codes

@copyright: Copyright (c) 2005 Open Source Applications Foundation
@license:   http://osafoundation.org/Chandler_0.1_license_terms.htm
"""

import M2Crypto.m2 as m2

from i18n import OSAFMessageFactory as _

certificateVerifyError = {
    m2.X509_V_ERR_UNABLE_TO_GET_ISSUER_CERT: _("unable to get issuer certificate"),
    m2.X509_V_ERR_UNABLE_TO_DECRYPT_CERT_SIGNATURE: _("unable to decrypt certificate's signature"),
    m2.X509_V_ERR_UNABLE_TO_DECODE_ISSUER_PUBLIC_KEY: _("unable to decode issuer public key"),
    m2.X509_V_ERR_CERT_SIGNATURE_FAILURE: _("certificate signature failure"),
    m2.X509_V_ERR_CERT_NOT_YET_VALID: _("certificate is not yet valid"),
    m2.X509_V_ERR_CERT_HAS_EXPIRED: _("certificate has expired"),
    m2.X509_V_ERR_ERROR_IN_CERT_NOT_BEFORE_FIELD: _("format error in certificate's notBefore field"),
    m2.X509_V_ERR_ERROR_IN_CERT_NOT_AFTER_FIELD: _("format error in certificate's notAfter field"),
    m2.X509_V_ERR_OUT_OF_MEM: _("out of memory"),
    m2.X509_V_ERR_DEPTH_ZERO_SELF_SIGNED_CERT: _("self signed certificate"),
    m2.X509_V_ERR_SELF_SIGNED_CERT_IN_CHAIN: _("self signed certificate in certificate chain"),
    m2.X509_V_ERR_UNABLE_TO_GET_ISSUER_CERT_LOCALLY: _("unable to get local issuer certificate"),
    m2.X509_V_ERR_UNABLE_TO_VERIFY_LEAF_SIGNATURE: _("unable to verify the first certificate"),
    m2.X509_V_ERR_INVALID_CA: _("invalid CA certificate"),
    m2.X509_V_ERR_PATH_LENGTH_EXCEEDED: _("path length constraint exceeded"),
    m2.X509_V_ERR_INVALID_PURPOSE: _("unsupported certificate purpose"),
    m2.X509_V_ERR_CERT_UNTRUSTED: _("certificate not trusted"),
    m2.X509_V_ERR_CERT_REJECTED: _("certificate rejected")
}

def getCertificateVerifyErrorString(code):
    """
    The the certificate verification/validation error string using the error code.
    """
    return certificateVerifyError.get(code, "%d" % code)

if __name__ == '__main__':
    assert getCertificateVerifyErrorString(m2.X509_V_ERR_UNABLE_TO_GET_ISSUER_CERT) == _("unable to get issuer certificate")
    assert getCertificateVerifyErrorString(m2.X509_V_OK) == "0"
