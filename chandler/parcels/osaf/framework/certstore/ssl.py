"""
Things to tie certificates into SSL/TLS connections.

@copyright: Copyright (c) 2005 Open Source Applications Foundation
@license:   http://osafoundation.org/Chandler_0.1_license_terms.htm
"""

import osaf.framework.certstore.certificate as certificate

from osaf.pim.collections import FilteredCollection


def loadCertificatesToContext(repView, ctx):
    """
    Add certificates to SSL Context.
    
    @param repView: repository view
    @param ctx: M2Crypto.SSL.Context
    """
    qName = 'sslCertificateQuery'
    q = repView.findPath('//userdata/%s' %(qName))
    if q is None:
        q = FilteredCollection(qName, view=repView)
        q.source = certificate.Certificate.getExtent(repView)
        q.filterExpression = u'item.type == "%s" and item.trust == %d' % (certificate.TYPE_ROOT, certificate.TRUST_AUTHENTICITY | certificate.TRUST_SITE)
        q.filterAttributes = ['type', 'trust']
        
    store = ctx.get_cert_store()
    for cert in q:
        store.add_x509(cert.asX509())
