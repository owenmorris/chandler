"""
Text storage unit tests
"""

__revision__  = "$Revision$"
__date__      = "$Date$"
__copyright__ = "Copyright (c) 2003 Open Source Applications Foundation"
__license__   = "http://osafoundation.org/Chandler_0.1_license_terms.htm"

import unittest, os

from repository.persistence.XMLRepository import XMLRepository

class TestText(unittest.TestCase):
    """ Test Text storage """

    def setUp(self):
        self.rootdir = os.environ['CHANDLERDIR']
        schemaPack = os.path.join(self.rootdir, 'repository',
                                  'packs', 'schema.pack')
        cineguidePack = os.path.join(self.rootdir, 'repository',
                                     'tests', 'data', 'packs',
                                     'cineguide.pack')
        self.rep = XMLRepository('TextUnitTest-Repository')
        self.rep.create()
        self.rep.loadPack(schemaPack)
        self.rep.loadPack(cineguidePack)

    def compressed(self, compression):
        khepburn = self.rep.find('//CineGuide/KHepburn')
        movie = khepburn.movies.first()
        self.assert_(movie is not None)

        largeText = os.path.join(self.rootdir, 'repository',
                                 'tests', 'data', 'world192.txt')

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

        self.rep.logger.info("%s compressed %d bytes to %d",
                             compression, count, len(movie.synopsis._data))

        self.rep.commit()
        self.rep.close()

        self.rep = XMLRepository('TextUnitTest-Repository')
        self.rep.open()

        khepburn = self.rep.find('//CineGuide/KHepburn')
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

        khepburn = self.rep.find('//CineGuide/KHepburn')
        movie = khepburn.movies.first()
        self.assert_(movie is not None)

        largeText = os.path.join(self.rootdir, 'repository',
                                 'tests', 'data', 'world192.txt')

        input = file(largeText, 'r')
        writer = movie.synopsis.getWriter(compression=compression)

        while True:
            data = input.read(1048576)
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

        self.rep.commit()
        self.rep.close()

        self.rep = XMLRepository('TextUnitTest-Repository')
        self.rep.open()

        khepburn = self.rep.find('//CineGuide/KHepburn')
        movie = khepburn.movies.first()
        self.assert_(movie is not None)

        input = file(largeText, 'r')
        reader = movie.synopsis.getReader()
        data = input.read()
        string = reader.read()
        input.close()
        reader.close()

        print len(data), len(string)
        self.assert_(data == string)
        
    def testAppendBZ2(self):

        self.appended('bz2')

    def testAppendZlib(self):

        self.appended('zlib')

    def testAppend(self):

        self.appended(None)

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
