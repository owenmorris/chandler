"""
Certificate import on startup

@copyright: Copyright (c) 2005 Open Source Applications Foundation
@license:   http://osafoundation.org/Chandler_0.1_license_terms.htm
"""

def installParcel(parcel, oldVersion=None):
    # Load cacert.pem into the repository

    from M2Crypto import X509, BIO, util
    from M2Crypto.EVP import MessageDigest
    import os, sys, time
    import logging
    
    log = logging.getLogger(__name__)
    
    chop = -1

    from application import schema
    cert = schema.ns('osaf.framework.certstore', parcel)
    lobType = schema.itemFor(schema.Lob, parcel.itsView)

    def fingerprint(x509):
        # XXX there is one in certificate.py
        der = x509.as_der()
        md = MessageDigest('sha1')
        md.update(der)
        digest = md.final()
        return hex(util.octx_to_num(digest))

    lastLine = ''
    pem = []

    certificates = 0
    
    for line in open(os.path.join(os.path.dirname(__file__),'cacert.pem'),'rU'):
        if line[:3] == '===':
            itsName = lastLine
            itsName = itsName[:chop]
        elif line[:chop] == '-----BEGIN CERTIFICATE-----':
            pem = [line]
        elif line[:chop] == '-----END CERTIFICATE-----':
            pem.append(line[:chop])
            x509 = X509.load_cert_string(''.join(pem))

            commonName = itsName
            itsName = itsName.replace('/', '_')

            if not x509.verify():
                subject = x509.get_subject()
                log.warn('Skipping certificate, does not verify: %s' % \
                         (subject.CN))
                #print x509.as_text()
                continue

            cert.Certificate.update(parcel, itsName,
                subjectCommonName = commonName,
                type='root', trust=3, fingerprintAlgorithm='sha1',
                fingerprint=fingerprint(x509),
                pem=lobType.makeValue(''.join(pem)),
                asText=lobType.makeValue(x509.as_text()),
            )
            pem = []
            certificates += 1

        elif pem:
            pem.append(line)

        lastLine = line

    log.info('Imported %d certificates' % certificates)
