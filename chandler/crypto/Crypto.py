__copyright__ = "Copyright (c) 2004 Open Source Applications Foundation"
_license__ = "http://osafoundation.org/Chandler_0.1_license_terms.htm"

import logging
from M2Crypto import RSA, X509, EVP, m2, Rand, Err, threading, BIO
import application.Globals as Globals
import Password

class Crypto(object):
    """
    Crypto services.
    """
    def __init__(self):
        self._randpool = 'randpool.dat'

    def _passphrase_callback(self, v):
        # XXX Need to ask from user
        return str(Password.Password('passw0rd'))

    def init(self):
        """
        The crypto services must be initialized before they can be used.
        """
        self._log = logging.getLogger('crypto')
        self._log.setLevel(logging.INFO)
        self._log.info('Starting crypto services')
    
        threading.init()
        # Generating entropy can be slow, so we should try to bootstrap
        # with something.
        # XXX Seems like this could be a security risk if someone else
        # XXX can read or place this file here?
        Rand.load_file(self._randpool, -1)

    def shutdown(self):
        """
        The crypto services must be shut down to clean things properly.
        You must reinitialize before using the crypto services again.
        """
        self._log.info('Stopping crypto services')

        Rand.save_file(self._randpool)
        threading.cleanup()

    def createRepositoryCertKey(self, force=False):
        """
        Calling this function ensures we will create repository
        certificate and private key if they do not yet exist.
        """
        self._log.info('Creating repository certificate and private key')

        storagePath = 'certificates'
        certName = 'Repository Certificate'
        
        caItem = Globals.repository.findPath('//' +
                                             storagePath + '/' + certName)
        if caItem is None or force:
            # Create storage area in db
            itemKind = Globals.repository.findPath('//Schema/Core/Item')
            certStorage = itemKind.newItem(storagePath, Globals.repository)
            
            # Create 'CA database'
            caKind = Globals.repository.findPath('//parcels/osaf/framework/crypto/CA')
            caItem = caKind.newItem('Repository CA', certStorage)
            caItem.lastSerialNumber = 0

            # Create private key and certificate
            import CA
            (cert, pkey, rsa) = CA.ca(caItem.lastSerialNumber + 1)
            self._pkey = pkey # XXX Shouldn't need this, see CA.ca()
            caItem.lastSerialNumber = caItem.lastSerialNumber + 1

            # Save certificate to db
            certKind = Globals.repository.findPath('//parcels/osaf/framework/crypto/Certificate')
            certItem = certKind.newItem(certName, certStorage)
            certItem.setPem(cert.as_pem(), x509=cert)
            certItem.setMarkedTrusted()

            # Save private key to db
            pkeyKind = Globals.repository.findPath('//parcels/osaf/framework/crypto/PrivateKey')
            pkeyItem = pkeyKind.newItem('Repository Private Key', certStorage)
            # There is no RSA.as_pem(), not sure if we need one
            buf = BIO.MemoryBuffer()
            rsa.save_key_bio(buf, cipher='aes_256_cbc', callback=self._passphrase_callback)
            pkeyItem.setPem(buf.read())
            #XXX These should be handled inside the PrivateKeyItem, by
            #XXX extracting from the RSA object itself
            pkeyItem.bits = 2048
            pkeyItem.isEncrypted = True
            pkeyItem.cipher = 'aes_256_cbc'

            # Set link in db between certificate and private key
            certItem.privateKey = pkeyItem

            Globals.repository.commit() # XXX Shouldn't need this

            self._pkey = None # XXX See where we set this
        
        self._log.info('Done creating repository certificate and private key')

