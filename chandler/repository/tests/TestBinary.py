"""
Binary storage unit tests
"""

__revision__  = "$Revision$"
__date__      = "$Date$"
__copyright__ = "Copyright (c) 2003 Open Source Applications Foundation"
__license__   = "http://osafoundation.org/Chandler_0.1_license_terms.htm"

import unittest, os

from repository.persistence.XMLRepository import XMLRepository

class TestBinary(unittest.TestCase):
    """ Test Binary storage """

    def setUp(self):
        rootdir = os.environ['CHANDLERDIR']
        schemaPack = os.path.join(rootdir, 'repository',
                                  'packs', 'schema.pack')
        cineguidePack = os.path.join(rootdir, 'repository',
                                     'tests', 'data', 'packs',
                                     'cineguide.pack')
        self.rep = XMLRepository('BinaryUnitTest-Repository')
        self.rep.create()
        self.rep.loadPack(schemaPack)
        self.rep.loadPack(cineguidePack)

    def testBZ2Compressed(self):
        khepburn = self.rep.find('//CineGuide/KHepburn')
        self.assert_(khepburn is not None)

        rootdir = os.environ['CHANDLERDIR']
        largeBinary = os.path.join(rootdir, 'repository',
                                   'tests', 'data', 'khepltr.jpg')

        input = file(largeBinary, 'r')
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

        self.rep.commit()
        self.rep.close()

        self.rep = XMLRepository('BinaryUnitTest-Repository')
        self.rep.open()

        khepburn = self.rep.find('//CineGuide/KHepburn')
        self.assert_(khepburn is not None)

        input = file(largeBinary, 'r')
        inputStream = khepburn.picture.getInputStream()
        data = input.read()
        picture = inputStream.read()
        input.close()
        inputStream.close()

        self.assert_(data == picture)

    def testZlibCompressed(self):
        khepburn = self.rep.find('//CineGuide/KHepburn')
        self.assert_(khepburn is not None)

        rootdir = os.environ['CHANDLERDIR']
        largeBinary = os.path.join(rootdir, 'repository',
                                   'tests', 'data', 'khepltr.jpg')

        input = file(largeBinary, 'r')
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

        self.rep.commit()
        self.rep.close()

        self.rep = XMLRepository('BinaryUnitTest-Repository')
        self.rep.open()

        khepburn = self.rep.find('//CineGuide/KHepburn')
        self.assert_(khepburn is not None)

        input = file(largeBinary, 'r')
        inputStream = khepburn.picture.getInputStream()
        data = input.read()
        picture = inputStream.read()
        input.close()
        inputStream.close()

        self.assert_(data == picture)

    def testUncompressed(self):
        khepburn = self.rep.find('//CineGuide/KHepburn')
        self.assert_(khepburn is not None)

        rootdir = os.environ['CHANDLERDIR']
        largeBinary = os.path.join(rootdir, 'repository',
                                   'tests', 'data', 'khepltr.jpg')

        input = file(largeBinary, 'r')
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

        self.rep.commit()
        self.rep.close()

        self.rep = XMLRepository('BinaryUnitTest-Repository')
        self.rep.open()

        khepburn = self.rep.find('//CineGuide/KHepburn')
        self.assert_(khepburn is not None)

        input = file(largeBinary, 'r')
        inputStream = khepburn.picture.getInputStream()
        data = input.read()
        picture = inputStream.read()
        input.close()
        inputStream.close()

        self.assert_(data == picture)
        
        
    def tearDown(self):
        self.rep.close()
        self.rep.delete()
        pass

if __name__ == "__main__":
#    import hotshot
#    profiler = hotshot.Profile('/tmp/TestItems.hotshot')
#    profiler.run('unittest.main()')
#    profiler.close()
    unittest.main()
