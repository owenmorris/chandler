from PyEGADS import egads
from M2Crypto import Rand
import threading
import logging

# XXX If PyEGADS is not available should do better job of using alternate
# XXX seeding strategies.

# XXX If Someone uses M2Crypto before we have seeded it with the desired
# XXX amount it can be a security risk. Should do something about that...

class Seeder(threading.Thread):
    """
    Seeder initializes the M2CRypto (OpenSSL) PRNG. Because gathering
    entropy can be slow this needs to run on its own thread in order
    to not block. Once the desired amount of entropy has been added,
    the seeder kills itself.
    """
    def run(self):
        log = logging.getLogger('m2seeder')

        log.setLevel(logging.INFO)

        log.info('Starting to seed M2Crypto.Rand')
        # How many bits to add per cycle, and how many bits to add, total,
        # until done
        # XXX Should be initialization parameters
        addBits = 32
        totalBits = 256

        # We need to bootstrap with something, because adding entropy
        # can be slow.
        # XXX Check what happens if randpool does not exist.
        Rand.load_file('randpool.dat', -1)
        try:
            e = egads.Egads()
            current = 0
            while (current < totalBits):
                Rand.rand_add(e.entropy(addBits), 1.0)
                current += addBits
                # XXX Is this too slow?
                Rand.save_file('randpool.dat')
                log.info('Added ' + str(addBits) + ' bits of entropy, now at '
                         + str(current) + ' bits')
        except Exception, err:
            log.info('Failed to seed M2Crypto.Rand, reason: ' + str(err))

        log.info('Done seeding M2Crypto.Rand')
