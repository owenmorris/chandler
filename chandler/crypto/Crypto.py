"""
Cryptographic services.

@copyright = Copyright (c) 2004 Open Source Applications Foundation
@license   = http://osafoundation.org/Chandler_0.1_license_terms.htm
"""

import logging
from M2Crypto import Rand, threading
import os

class Crypto(object):
    """
    Crypto services.
    """
    def __init__(self, certificateDir):
        assert certificateDir != None
        self._randpool = os.path.join(certificateDir, 'randpool.dat')
        self.certificateDir = certificateDir

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
        Rand.load_file(self._randpool, -1)

    def shutdown(self):
        """
        The crypto services must be shut down to clean things properly.
        You must reinitialize before using the crypto services again.
        """
        self._log.info('Stopping crypto services')

        # XXX Check return value and log if we failed to write data
        Rand.save_file(self._randpool)
        threading.cleanup()
