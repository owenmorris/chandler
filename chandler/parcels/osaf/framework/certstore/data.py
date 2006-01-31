"""
Certificate import on startup

@copyright: Copyright (c) 2005 Open Source Applications Foundation
@license:   http://osafoundation.org/Chandler_0.1_license_terms.htm
"""
from application import schema
import sys


def loadCerts(parcel, moduleName, filename=u'cacert.pem'):
    # Load cacert.pem into the repository

    import os, sys
    import logging

    from M2Crypto import X509, util
    from M2Crypto.EVP import MessageDigest

    log = logging.getLogger(__name__)

    #Encode the unicode filename to the system character set encoding
    filename = filename.encode(sys.getfilesystemencoding())

    chop = -1

    cert = schema.ns('osaf.framework.certstore', parcel)
    lobType = schema.itemFor(schema.Lob, parcel.itsView)

    from osaf.framework.certstore import utils

    lastLine = ''
    pem = []

    certificates = 0
    itsName = None
    
    for line in open(
        os.path.join(
            os.path.dirname(sys.modules[moduleName].__file__),filename
        ), 'rU'
    ):
        if line[:3] == '===':
            itsName = lastLine
            itsName = itsName[:chop]
        elif line[:chop] == '-----BEGIN CERTIFICATE-----':
            pem = [line]
        elif line[:chop] == '-----END CERTIFICATE-----':
            pem.append(line[:chop])
            x509 = X509.load_cert_string(''.join(pem))

            if itsName is not None:
                commonName = itsName
                itsName = itsName.replace('/', '_')
            else:
                commonName = x509.get_subject().commonName or ''

            if not x509.verify():
                log.warn('Skipping certificate, does not verify: %s' % \
                         (commonName))
                #print x509.as_text()
                continue

            #XXX [i18n] Can a commonName contain non-ascii characters?
            cert.Certificate.update(parcel, itsName,
                displayName = unicode(commonName),
                type='root',#cert.TYPE_ROOT, 
                trust=3,#cert.TRUST_AUTHENTICITY | cert.TRUST_SITE, 
                fingerprintAlgorithm='sha1',
                fingerprint=utils.fingerprint(x509),
                pem=lobType.makeValue(''.join(pem)),
                asText=lobType.makeValue(x509.as_text()),
            )
            pem = []
            certificates += 1
            itsName = None

        elif pem:
            pem.append(line)

        lastLine = line

    log.info(
        'Imported %d certificates from %s in %s',
        certificates, filename, moduleName
    )


def installParcel(parcel, oldVersion=None):

    loadCerts(parcel, __name__)
    
    from osaf.pim.collections import KindCollection

    cert = schema.ns('osaf.framework.certstore', parcel)
    kind = schema.itemFor(cert.Certificate, parcel.itsView)
    KindCollection.update(kind, 'fullExtent',  kind=kind, recursive=True)
    KindCollection.update(kind, 'exactExtent', kind=kind, recursive=False)
 

