"""
Binary storage unit tests
"""

__revision__  = "$Revision$"
__date__      = "$Date$"
__copyright__ = "Copyright (c) 2003 Open Source Applications Foundation"
__license__   = "http://osafoundation.org/Chandler_0.1_license_terms.htm"

import unittest, os

from repository.persistence.XMLRepository import XMLRepository
from repository.tests.RepositoryTestCase import RepositoryTestCase


class TestBinary(RepositoryTestCase):
    """ Test Binary storage """

    def setUp(self):

        super(TestBinary, self).setUp()

        cineguidePack = os.path.join(self.testdir, 'data', 'packs',
                                     'cineguide.pack')
        self.rep.loadPack(cineguidePack)
        self.rep.commit()

    def testBZ2Compressed(self):
        khepburn = self._find('//CineGuide/KHepburn')
        self.assert_(khepburn is not None)

        largeBinary = os.path.join(self.testdir, 'data', 'khepltr.jpg')

        input = file(largeBinary, 'rb')
        binary = khepburn.getAttributeAspect('picture', 'type').makeValue(None, mimetype='image/jpg')
        outputStream = binary.getOutputStream(compression='bz2')
        
        count = 0
        while True:
            data = input.read(1048576)
            if len(data) > 0:
                outputStream.write(data)
                count += len(data)
            else:
                break

        input.close()
        outputStream.close()
        khepburn.picture = binary

        self.rep.logger.info("bz2 compressed %d bytes to %d", count,
                             len(khepburn.picture._data))

        self._reopenRepository()

        khepburn = self._find('//CineGuide/KHepburn')
        self.assert_(khepburn is not None)

        input = file(largeBinary, 'rb')
        inputStream = khepburn.picture.getInputStream()
        data = input.read()
        picture = inputStream.read()
        input.close()
        inputStream.close()

        self.assert_(data == picture)

    def testZlibCompressed(self):
        khepburn = self._find('//CineGuide/KHepburn')
        self.assert_(khepburn is not None)

        largeBinary = os.path.join(self.testdir, 'data', 'khepltr.jpg')

        input = file(largeBinary, 'rb')
        binary = khepburn.getAttributeAspect('picture', 'type').makeValue(None, mimetype='image/jpg')
        outputStream = binary.getOutputStream(compression='zlib')
        
        count = 0
        while True:
            data = input.read(1048576)
            if len(data) > 0:
                outputStream.write(data)
                count += len(data)
            else:
                break

        input.close()
        outputStream.close()
        khepburn.picture = binary
        
        self.rep.logger.info("zlib compressed %d bytes to %d", count,
                             len(khepburn.picture._data))

        self._reopenRepository()

        khepburn = self._find('//CineGuide/KHepburn')
        self.assert_(khepburn is not None)

        input = file(largeBinary, 'rb')
        inputStream = khepburn.picture.getInputStream()
        data = input.read()
        picture = inputStream.read()
        input.close()
        inputStream.close()

        self.assert_(data == picture)

    def testUncompressed(self):
        khepburn = self._find('//CineGuide/KHepburn')
        self.assert_(khepburn is not None)

        largeBinary = os.path.join(self.testdir, 'data', 'khepltr.jpg')

        input = file(largeBinary, 'rb')
        binary = khepburn.getAttributeAspect('picture', 'type').makeValue(None, mimetype='image/jpg')
        outputStream = binary.getOutputStream(compression=None)
        
        while True:
            data = input.read(1048576)
            if len(data) > 0:
                outputStream.write(data)
            else:
                break

        input.close()
        outputStream.close()
        khepburn.picture = binary

        self._reopenRepository()

        khepburn = self._find('//CineGuide/KHepburn')
        self.assert_(khepburn is not None)

        input = file(largeBinary, 'rb')
        inputStream = khepburn.picture.getInputStream()
        data = input.read()
        picture = inputStream.read()
        input.close()
        inputStream.close()

        self.assert_(data == picture)
        

if __name__ == "__main__":
#    import hotshot
#    profiler = hotshot.Profile('/tmp/TestBinary.hotshot')
#    profiler.run('unittest.main()')
#    profiler.close()
    unittest.main()
