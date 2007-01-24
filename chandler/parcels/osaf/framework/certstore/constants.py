#   Copyright (c) 2003-2007 Open Source Applications Foundation
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
Certificate constants

@var TRUST_NONE:         The certificate is not trusted at all, and will not
                         be used for any operation.
@var TRUST_AUTHENTICITY: Is the certificate trusted to be authentic. In
                         practice this means whether or not the certificate
                         will be used or not. Applies to Certificate Kind's
                         trust attribute. Any type of certificate can have
                         this bit set.
@var TRUST_SERVER:       Is the certificate trusted to issue server certificate.
                         In practice this means whether or not the certificate
                         is included in the trusted root (or Certificate
                         Authority) list. Applies to Certificate Kind's
                         trust attribute. Applies only to root certificates.    

@var PURPOSE_CA:         Is the certificate a root (i.e. Certificate Authority)
                         certificate. Applies to Certificate Kind's
                         purpose attribute.
@var PURPOSE_SERVER:     Is the certificate a site certificate (i.e. issued for
                         a specific computer with a name, for example
                         www.example.com). Applies to Certificate Kind's
                         purpose attribute.    
"""

TRUST_NONE         = 0
TRUST_AUTHENTICITY = 1
TRUST_SERVER       = 2

PURPOSE_CA         = 1
PURPOSE_SERVER     = 2
