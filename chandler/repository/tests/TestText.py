"""
Text storage unit tests
"""

__revision__  = "$Revision$"
__date__      = "$Date$"
__copyright__ = "Copyright (c) 2003 Open Source Applications Foundation"
__license__   = "http://osafoundation.org/Chandler_0.1_license_terms.htm"

import unittest, os

from repository.persistence.XMLRepository import XMLRepository
from repository.tests.RepositoryTestCase import RepositoryTestCase


class TestText(RepositoryTestCase):
    """ Test Text storage """

    def setUp(self):

        super(TestText, self).setUp()

        cineguidePack = os.path.join(self.testdir, 'data', 'packs',
                                     'cineguide.pack')
        self.rep.loadPack(cineguidePack)
        self.rep.commit()

    def compressed(self, compression):
        khepburn = self.rep.findPath('//CineGuide/KHepburn')
        movie = khepburn.movies.first()
        self.assert_(movie is not None)

        largeText = os.path.join(self.testdir, 'data', 'world192.txt')

        input = file(largeText, 'r')
        writer = movie.synopsis.getWriter(compression=compression)

        count = 0
        while True:
            data = input.read(1048576)
            if len(data) > 0:
                writer.write(data)
                count += len(data)
            else:
                break

        input.close()
        writer.close()
        movie.setDirty()
        
        self.rep.logger.info("%s compressed %d bytes to %d",
                             compression, count, len(movie.synopsis._data))

        self._reopenRepository()

        khepburn = self.rep.findPath('//CineGuide/KHepburn')
        movie = khepburn.movies.first()
        self.assert_(movie is not None)

        input = file(largeText, 'r')
        reader = movie.synopsis.getReader()
        data = input.read()
        string = reader.read()
        input.close()
        reader.close()

        self.assert_(data == string)

    def testBZ2Compressed(self):

        self.compressed('bz2')
       
    def testZlibCompressed(self):

        self.compressed('zlib')
        
    def testUncompressed(self):

        self.compressed(None)

    def appended(self, compression):

        khepburn = self.rep.findPath('//CineGuide/KHepburn')
        movie = khepburn.movies.first()
        self.assert_(movie is not None)

        largeText = os.path.join(self.testdir, 'data', 'world192.txt')

        input = file(largeText, 'r')
        writer = movie.synopsis.getWriter(compression=compression)

        while True:
            data = input.read(548576)
            if len(data) > 0:
                writer.write(data)
                movie.setDirty()
                writer.close()
                self.rep.commit()
                writer = movie.synopsis.getWriter(compression=compression,
                                                  append=True)
            else:
                break

        input.close()
        writer.close()

        self._reopenRepository()

        khepburn = self.rep.findPath('//CineGuide/KHepburn')
        movie = khepburn.movies.first()
        self.assert_(movie is not None)

        input = file(largeText, 'r')
        reader = movie.synopsis.getReader()
        data = input.read()
        string = reader.read()
        input.close()
        reader.close()

        self.assert_(data == string)
        
    def testAppendBZ2(self):

        self.appended('bz2')

    def testAppendZlib(self):

        self.appended('zlib')

    def testAppend(self):

        self.appended(None)


if __name__ == "__main__":
#    import hotshot
#    profiler = hotshot.Profile('/tmp/TestItems.hotshot')
#    profiler.run('unittest.main()')
#    profiler.close()
#    unittest.main()
    pass
