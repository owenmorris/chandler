"""
Cryptographic services.

@copyright = Copyright (c) 2004 Open Source Applications Foundation
@license   = http://osafoundation.org/Chandler_0.1_license_terms.htm
"""

import logging
import os
from M2Crypto import Rand, threading
import ssl

class Crypto(object):
    """
    Crypto services.
    """
    def init(self, profileDir):
        """
        The crypto services must be initialized before they can be used.
        """
        assert profileDir
        self.profileDir = profileDir

        self._log = logging.getLogger('crypto')
        self._log.setLevel(logging.INFO)
        self._log.info('Starting crypto services')
    
        threading.init()

        # Generating entropy can be slow, so we should try to bootstrap
        # with something.
        self._randpool = os.path.join(profileDir, 'randpool.dat')
        Rand.load_file(self._randpool, -1)

        ssl.init(profileDir)

    def shutdown(self):
        """
        The crypto services must be shut down to clean things properly.
        You must reinitialize before using the crypto services again.
        """
        self._log.info('Stopping crypto services')

        # XXX Check return value and log if we failed to write data
        Rand.save_file(self._randpool)
        threading.cleanup()

    def getSSLContext(self, protocol='sslv23', verify=True,
                      verifyCallback=None):
        """
        Get an SSL Context.
        """
        return ssl.getContext(self.profileDir, protocol, verify,
                              verifyCallback, )

    def getSSLClientContextFactory(self, method='sslv23', verify=True,
                                   verifyCallBack=None):
        """
        Get an SSL Context factory.
        """
        return ssl.ClientContextFactory(self.profileDir, method, verify,
                                        verifyCallBack)
