__copyright__ = "Copyright (c) 2004 Open Source Applications Foundation"
__license__   = "http://osafoundation.org/Chandler_0.1_license_terms.htm"

import application.Globals as Globals
from repository.item.Item import Item
from M2Crypto import X509, BIO, util
from M2Crypto.EVP import MessageDigest
import mx.DateTime as DateTime
from email.Utils import parsedate

class CertificateItem(Item):
    def __init__(self, *args):
        super(CertificateItem, self).__init__(*args)
        self._x509 = None

    def getName(self):
        return self.getItemDisplayName()
    
    def _calculateFingerprint(self, md='sha1', format='human'):
        if format is not 'human':
            raise NotImplementedError

        der = self._x509.as_der()
        md = MessageDigest(md)
        md.update(der)
        digest = md.final()

        hexstr = hex(util.octx_to_num(digest))
        fingerprint = hexstr[2:len(hexstr)-1]
        list = [fingerprint[x:x+2] for x in range(len(fingerprint)) if x%2 == 0]
        self.fingerprint = ':'.join(list)

    def getMarkedTrusted(self):
        # XXX We may want to check dynamically if we have signed this instead
        return self.markedTrusted

    def setMarkedTrusted(self, trusted=True):
        self.markedTrusted = trusted

    def _extractAsText(self):
        self.asText = self._x509.as_text()
        
    def _extractVersion(self):
        self.version = self._x509.get_version()
        
    def _extractSerial(self):
        self.serialNumber = self._x509.get_serial_number()
        
    def _extractNotBefore(self):
        # XXX Is there a simpler way to handle date?
        self.notBefore = DateTime.mktime(parsedate(str(self._x509.get_not_before())))
        
    def _extractNotAfter(self):
        # XXX Is there a simpler way to handle date?
        self.notAfter = DateTime.mktime(parsedate(str(self._x509.get_not_after())))

    def _extractIssuer(self):
        self.issuer = self._x509.get_issuer().CN
        
    def _extractSubject(self):
        self.subject = self._x509.get_subject().CN        

    def getPem(self, type='str'):
        """
        Get the PEM value. You can specify the type in the type attribute.
        """
        if type is 'str':
            return self.pem.getReader().read()
        if type is 'Text':
            return self.pem
        
        raise ValueError, 'illegal type value'

    def setPem(self, pem, x509=None):
        text = self.getAttributeAspect('pem',
                                       'type').makeValue(pem, compression=None)
        self.pem = text

        if x509 is None:
            buf = BIO.MemoryBuffer(pem)
            self._x509 = X509.load_cert_bio(buf)
        else:
            self._x509 = x509

        # XXX These should probably be done on demand
        if self._x509:
            self._calculateFingerprint()
            self._extractAsText()
            self._extractVersion()
            self._extractSerial()
            self._extractNotBefore()
            self._extractNotAfter()
            self._extractIssuer()
            self._extractSubject()
            
            
