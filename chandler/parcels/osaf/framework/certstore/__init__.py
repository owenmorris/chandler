#   Copyright (c) 2003-2006 Open Source Applications Foundation
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


from certificate import *

def installParcel(parcel, oldVersion=None):
    # load our subparcels
    from application import schema
    schema.synchronize(parcel.itsView, "osaf.framework.certstore.data")
    schema.synchronize(parcel.itsView, "osaf.framework.certstore.blocks")

    from osaf.pim.collections import FilteredCollection
    import certificate, utils

    FilteredCollection.update(parcel, 'sslCertificateQuery',
        source=utils.getExtent(certificate.Certificate, parcel.itsView),
        filterExpression=u"view.findValues(uuid, ('type', None), ('trust', None)) == ('%s', %d)" %(constants.TYPE_ROOT, constants.TRUST_AUTHENTICITY | constants.TRUST_SITE),
        filterAttributes=['type', 'trust']
    )
    
    FilteredCollection.update(parcel, 'sslTrustedSiteCertificatesQuery',
        source=utils.getExtent(certificate.Certificate, parcel.itsView),
        filterExpression=u"view.findValues(uuid, ('type', None), ('trust', None)) == ('%s', %d)" %(constants.TYPE_SITE, constants.TRUST_AUTHENTICITY),
        filterAttributes=['type', 'trust']
    )
