__copyright__ = "Copyright (c) 2004 Open Source Applications Foundation"
__license__   = "http://osafoundation.org/Chandler_0.1_license_terms.htm"

import application.Globals as Globals
from repository.item.Item import Item
from M2Crypto import RSA, BIO

class PrivateKeyItem(Item):

    def __init__(self, *args):
        super(PrivateKeyItem, self).__init__(*args)
        self._rsa = None

    def getName(self):
        return self.getItemDisplayName()
    
    def getPem(self, type='str'):
        """
        Get the PEM value. You can specify the type in the type attribute.
        """
        if type is 'str':
            return self.pem.getReader().read()
        if type is 'Text':
            return self.pem
        
        raise ValueError, 'illegal type value'

    def setPem(self, pem, rsa=None):
        text = self.getAttributeAspect('pem',
                                       'type').makeValue(pem, compression=None)
        self.pem = text

        if rsa is None:
            buf = BIO.MemoryBuffer(pem)
            self._rsa = RSA.load_key_bio(buf,
                                         Globals.crypto._passphrase_callback)
        else:
            self._rsa = rsa
