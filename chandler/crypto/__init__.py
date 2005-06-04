"""
Cryptographic services.

@copyright: Copyright (c) 2005 Open Source Applications Foundation
@license:   http://osafoundation.org/Chandler_0.1_license_terms.htm
"""

import os
import M2Crypto.Rand as Rand
import M2Crypto.threading as m2threading

def startup(profileDir):
    """
    Initialize the cryptographic services before doing any other
    cryptographic operations.
    
    @param profileDir: The profile directory. Additional entropy will be loaded
                       from a file in this directory. It is not a fatal error
                       if the file does not exist.
    """
    m2threading.init()
    Rand.load_file(_randpoolPath(profileDir), -1)
    
    
def shutdown(profileDir):
    """
    Shut down the cryptographic services. You must call startup()
    before doing cryptographic operations again.
    
    @param profileDir: The profile directory. A snapshot of current entropy
                       state will be saved into a file in this directory. 
                       It is not a fatal error if the file cannot be created.
    """
    Rand.save_file(_randpoolPath(profileDir))
    m2threading.cleanup()


def _randpoolPath(profileDir):
    # Return the absolute path for the file that we use to load
    # initial entropy from in startup/store entropy into in
    # shutdown.
    return os.path.join(profileDir, 'randpool.dat')
