# A script to convert pem format cacert.pem into parcel.xml
# Works on Cygwin with Unix line feeds (at least)

from M2Crypto import X509, BIO, util
from M2Crypto.EVP import MessageDigest
import os, sys, time

if os.name == 'posix':
    chop = -2
else:
    chop = -1

def fingerprint(x509):
    der = x509.as_der()
    md = MessageDigest('sha1')
    md.update(der)
    digest = md.final()
    return hex(util.octx_to_num(digest))

o = open('_parcel.xml', 'w')

o.write('<?xml version="1.0" encoding="iso-8859-1"?>\n\n' +
'<Parcel xmlns="parcel:core"\n' +
'        xmlns:cert="parcel:osaf.framework.certstore.schema">\n\n')

lastLine = ''
pem = ''

for line in open('cacert.pem'):
    if line[:3] == '===':
        itsName = lastLine
        itsName = itsName[:chop]
    elif line[:chop] == '-----BEGIN CERTIFICATE-----':
        pem = line.replace('\r', '')
    elif line[:chop] == '-----END CERTIFICATE-----':
        pem += line[:chop]
        x509 = X509.load_cert_string(pem)
        if not x509.verify():
            subject = x509.get_subject()
            print 'Skipping, does not verify:', subject.O, subject.CN
            #print x509.as_text()
            continue
        # More tests, although verify() should have caught these
        after = x509.get_not_after()
        try:
            if time.gmtime() > time.strptime(str(after), '%b %d %H:%M:%S %Y %Z'):
                subject = x509.get_subject()
                print 'Skipping expired:', subject.O, subject.CN, after
                #print x509.as_text()
                continue
        except ValueError:
            print 'ERROR: Bad certificate format (skipping)'
            #print x509.as_text()
            continue
        
        o.write('  <cert:Certificate itsName="%s">\n' % (itsName.replace('/', '_')))
        commonName = itsName.replace('&', '&amp;')
        commonName = commonName.replace('<', '&gt;')
        o.write('  <subjectCommonName>%s</subjectCommonName>\n' %(commonName))
        o.write('  <type value="root"/>\n')        
        o.write('  <trust value="3"/>\n')#auth, site
        o.write('  <fingerprintAlgorithm value="sha1"/>\n')
        o.write('  <fingerprint value="%s"/>\n' %(fingerprint(x509)))
        o.write('  <pem>%s</pem>\n' %(pem))
        o.write('  <asText>%s</asText>\n' %(x509.as_text()))
        o.write('  </cert:Certificate>\n\n')
        pem = ''
    elif pem != '':
        pem += line.replace('\r', '')
    lastLine = line

o.write('</Parcel>\n')
o.close()
    
