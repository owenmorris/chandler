__copyright__ = "Copyright (c) 2003 Open Source Applications Foundation"
_license__ = "http://osafoundation.org/Chandler_0.1_license_terms.htm"

import logging
from M2Crypto import RSA, X509, EVP, m2, Rand, Err, threading

class Crypto(object):
    """
    Crypto services.
    """
    def __init__(self):
        self._randpool = 'randpool.dat'

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
