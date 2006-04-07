"""
Certificate constants

@copyright: Copyright (c) 2005 Open Source Applications Foundation
@license:   http://osafoundation.org/Chandler_0.1_license_terms.htm

@var TRUST_AUTHENTICITY: Is the certificate trusted to be authentic. In
                         practice this means whether or not the certificate
                         will be used or not. Applies to Certificate Kind's
                         trust attribute. Any type of certificate can have
                         this bit set.
@var TRUST_SITE:         Is the certificate trusted to issue site certificate.
                         In practice this means whether or not the certificate
                         is included in the trusted root (or Certificate
                         Authority) list. Applies to Certificate Kind's
                         trust attribute. Applies only to root certificates.    

@var TYPE_ROOT:          Is the certificate a root (i.e. Certificate Authority)
                         certificate. Applies to Certificate Kind's
                         type attribute.
@var TYPE_SITE:          Is the certificate a site certificate (i.e. issued for
                         a specific computer with a name, for example
                         www.example.com). Applies to Certificate Kind's
                         type attribute.    
"""

TRUST_AUTHENTICITY = 1
TRUST_SITE         = 2

TYPE_ROOT          = 'root'
TYPE_SITE          = 'site'
