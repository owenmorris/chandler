"""
Text blocked read of appended storage compression unit tests
"""

__revision__  = "$Revision$"
__date__      = "$Date$"
__copyright__ = "Copyright (c) 2003-2004 Open Source Applications Foundation"
__license__   = "http://osafoundation.org/Chandler_0.1_license_terms.htm"

import unittest, os

from cStringIO import StringIO

from repository.persistence.XMLRepository import XMLRepository
from repository.tests.RepositoryTestCase import RepositoryTestCase


class TestBZ2(RepositoryTestCase):
    """ Test Text storage """

    def setUp(self):

        super(TestBZ2, self).setUp()

        cineguidePack = os.path.join(self.testdir, 'data', 'packs',
                                     'cineguide.pack')
        self.rep.loadPack(cineguidePack)
        self.rep.commit()

    def appended(self, compression):

        khepburn = self.rep.findPath('//CineGuide/KHepburn')
        movie = khepburn.movies.first()
        self.assert_(movie is not None)

        largeText = os.path.join(self.testdir, 'data', 'world192.txt')

        input = file(largeText, 'r')
        movie.synopsis._indexed = False
        writer = movie.synopsis.getWriter(compression=compression)

        while True:
            data = input.read(54857)
            if len(data) > 0:
                writer.write(data)
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

        buffer = StringIO()
        while True:
            data = reader.read(504)
            if len(data) > 0:
                buffer.write(data)
            else:
                break
            
        data = buffer.getvalue()
        buffer.close()

        string = input.read()
        input.close()
        reader.close()

        self.assert_(data == string)
        
    def testAppendBZ2(self):

        self.appended('bz2')

    def testAppendZlib(self):

        self.appended('zlib')


if __name__ == "__main__":
#    import hotshot
#    profiler = hotshot.Profile('/tmp/TestItems.hotshot')
#    profiler.run('unittest.main()')
#    profiler.close()
    unittest.main()
