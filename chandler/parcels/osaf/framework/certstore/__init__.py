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


from certificate import *
from chandlerdb.item.Item import Item

class TrustedCACertsFilter(Item):
    def isTrustedCACert(self, view, uuid):
        purpose, trust = view.findValues(uuid, ('purpose', 0), ('trust', 0))
        return purpose & constants.PURPOSE_CA and \
               trust & constants.TRUST_AUTHENTICITY | constants.TRUST_SERVER

class TrustedServerCertsFilter(Item):
    def isTrustedServerCert(self, view, uuid):
        purpose, trust = view.findValues(uuid, ('purpose', 0), ('trust', 0))
        return purpose & constants.PURPOSE_SERVER and \
               trust & constants.TRUST_AUTHENTICITY

def installParcel(parcel, oldVersion=None):
    # load our subparcels
    from application import schema
    schema.synchronize(parcel.itsView, "osaf.framework.certstore.data")
    schema.synchronize(parcel.itsView, "osaf.framework.certstore.blocks")

    from osaf.pim.collections import FilteredCollection
    import certificate, utils

    FilteredCollection.update(parcel, 'sslCertificateQuery',
        source=utils.getExtent(certificate.Certificate, parcel.itsView),
        filterMethod=(TrustedCACertsFilter(None, parcel), 'isTrustedCACert'),
        filterAttributes=['purpose', 'trust']
    )
    
    FilteredCollection.update(parcel, 'sslTrustedServerCertificatesQuery',
        source=utils.getExtent(certificate.Certificate, parcel.itsView),
        filterMethod=(TrustedServerCertsFilter(None, parcel),
                      'isTrustedServerCert'),
        filterAttributes=['purpose', 'trust']
    )
