"""
SSL

@copyright: Copyright (c) 2005 Open Source Applications Foundation
@license:   http://osafoundation.org/Chandler_0.1_license_terms.htm
"""

import osaf.framework.certstore.certificate as certificate
import osaf.framework.certstore.notification as notification

# XXX Should be done using ref collections instead?
import repository.query.Query as Query


def addCertificates(repView, ctx):
    """
    Add certificates to SSL Context.
    
    @param repView: repository view
    @param ctx: SSL.Context
    """
    
    qName = 'sslCertificateQuery'
    q = repView.findPath('//Queries/%s' %(qName))
    if q is None:
        p = repView.findPath('//Queries')
        k = repView.findPath('//Schema/Core/Query')
        q = Query.Query(qName, p, k, u'for i in "//parcels/osaf/framework/certstore/schema/Certificate" where i.type == "root" and i.trust == %d' % (certificate.TRUST_AUTHENTICITY | certificate.TRUST_SITE))
        notificationItem = repView.findPath('//parcels/osaf/framework/certstore/schema/dummyCertNotification')
        q.subscribe(notificationItem, 'handle', True, True)
        
    store = ctx.get_cert_store()
    for cert in q:
        store.add_x509(cert.asX509())
