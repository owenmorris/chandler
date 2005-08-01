def installParcel(parcel, oldVersion=None):
    # Load cacert.pem into the repository

    from M2Crypto import X509, BIO, util
    from M2Crypto.EVP import MessageDigest
    import os, sys, time
    chop = -1

    from application import schema
    cert = schema.ns('osaf.framework.certstore', parcel)
    lobType = schema.itemFor(schema.Lob, parcel.itsView)

    def fingerprint(x509):
        der = x509.as_der()
        md = MessageDigest('sha1')
        md.update(der)
        digest = md.final()
        return hex(util.octx_to_num(digest))

    lastLine = ''
    pem = []

    for line in open(os.path.join(os.path.dirname(__file__),'cacert.pem'),'rU'):
        if line[:3] == '===':
            itsName = lastLine
            itsName = itsName[:chop]
        elif line[:chop] == '-----BEGIN CERTIFICATE-----':
            pem = [line]
        elif line[:chop] == '-----END CERTIFICATE-----':
            pem.append(line[:chop])
            x509 = X509.load_cert_string(''.join(pem))

            commonName = itsName.replace('&', '&amp;')
            commonName = commonName.replace('<', '&gt;')
            itsName = commonName.replace('/', '_')

            if not x509.verify():
                subject = x509.get_subject()
                # XXX log message?  remove old certificate?
                #print 'Skipping, does not verify:', subject.O, subject.CN
                #print x509.as_text()
                continue

            # More tests, although verify() should have caught these
            after = x509.get_not_after()
            try:
                if time.gmtime() > time.strptime(str(after), '%b %d %H:%M:%S %Y %Z'):
                    subject = x509.get_subject()
                    # XXX log message?  remove old certificate?
                    #print 'Skipping expired:', subject.O, subject.CN, after
                    #print x509.as_text()
                    continue
            except ValueError:
                # XXX log message?  remove old certificate?
                #print 'ERROR: Bad certificate format (skipping)'
                #print x509.as_text()
                continue

            cert.Certificate.update(parcel, itsName,
                subjectCommonName = commonName,
                type="root", trust=3, fingerprintAlgorithm="sha1",
                fingerprint=fingerprint(x509),
                pem=lobType.makeValue(''.join(pem)),
                asText=lobType.makeValue(x509.as_text()),
            )
            pem = []

        elif pem:
            pem.append(line)

        lastLine = line

