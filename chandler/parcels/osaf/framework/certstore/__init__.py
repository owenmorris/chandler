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
