#   Copyright (c) 2003-2007 Open Source Applications Foundation
#
#   Licensed under the Apache License, Version 2.0 (the "License");
#   you may not use this file except in compliance with the License.
#   You may obtain a copy of the License at
#
#       http://www.apache.org/licenses/LICENSE-2.0
#
#   Unless required by applicable law or agreed to in writing, software
#   distributed under the License is distributed on an "AS IS" BASIS,
#   WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
#   See the License for the specific language governing permissions and
#   limitations under the License.

"""
Text storage unit tests
"""

import unittest, os
from pkg_resources import resource_stream

from chandlerdb.util.RepositoryTestCase import RepositoryTestCase
from chandlerdb.util.c import UUID

class TestText(RepositoryTestCase):
    """ Test Text storage """

    def setUp(self):

        super(TestText, self).setUp()
        self.loadCineguide(self.view)

    def compressed(self, compression, encryption, key):
        view = self.view
        khepburn = view.findPath('//CineGuide/KHepburn')
        movie = khepburn.movies.first()
        self.assert_(movie is not None)

        input = resource_stream('tests', 'data/world192.txt')
        movie.synopsis.mimetype = 'text/plain'
        writer = movie.synopsis.getWriter(compression=compression,
                                          encryption=encryption,
                                          key=key)

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

        self._reopenRepository()
        view = self.view

        khepburn = view.findPath('//CineGuide/KHepburn')
        movie = khepburn.movies.first()
        self.assert_(movie is not None)

        input = resource_stream('tests', 'data/world192.txt')
        reader = movie.synopsis.getReader(key)
        data = input.read()
        string = reader.read()
        input.close()
        reader.close()

        self.assert_(data == string)

    def testBZ2Compressed(self):

        self.compressed('bz2', None, None)
       
    def testBZ2Encrypted(self):

        self.compressed('bz2', 'rijndael', UUID()._uuid)
       
    def testZlibCompressed(self):

        self.compressed('zlib', None, None)
        
    def testZlibEncrypted(self):

        self.compressed('zlib', 'rijndael', UUID()._uuid)
        
    def testUncompressed(self):

        self.compressed(None, None, None)

    def testEncrypted(self):

        self.compressed(None, 'rijndael', UUID()._uuid)

    def appended(self, compression, encryption, key):

        view = self.view
        khepburn = view.findPath('//CineGuide/KHepburn')
        movie = khepburn.movies.first()
        self.assert_(movie is not None)

        input = resource_stream('tests', 'data/world192.txt')
        movie.synopsis.mimetype = 'text/plain'
        writer = movie.synopsis.getWriter(compression=compression,
                                          encryption=encryption,
                                          key=key)

        while True:
            data = input.read(548576)
            if len(data) > 0:
                writer.write(data)
                writer.close()
                view.commit()
                writer = movie.synopsis.getWriter(compression=compression,
                                                  encryption=encryption,
                                                  key=key, append=True)
            else:
                break

        input.close()
        writer.close()

        self._reopenRepository()
        view = self.view

        khepburn = view.findPath('//CineGuide/KHepburn')
        movie = khepburn.movies.first()
        self.assert_(movie is not None)

        input = resource_stream('tests', 'data/world192.txt')
        reader = movie.synopsis.getReader(key)
        data = input.read()
        string = reader.read()
        input.close()
        reader.close()

        self.assert_(data == string)
        
    def testAppendBZ2(self):

        self.appended('bz2', None, None)

    def testAppendBZ2Encrypted(self):

        self.appended('bz2', 'rijndael', UUID()._uuid)

    def testAppendZlib(self):

        self.appended('zlib', None, None)

    def testAppendZlibEncrypted(self):

        self.appended('zlib', 'rijndael', UUID()._uuid)

    def testAppend(self):

        self.appended(None, None, None)

    def testAppendEncrypted(self):

        self.appended(None, 'rijndael', UUID()._uuid)


if __name__ == "__main__":
#    import hotshot
#    profiler = hotshot.Profile('/tmp/TestItems.hotshot')
#    profiler.run('unittest.main()')
#    profiler.close()
    unittest.main()
