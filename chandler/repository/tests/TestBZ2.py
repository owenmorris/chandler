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
Text blocked read of appended storage compression unit tests
"""

import unittest, os

from cStringIO import StringIO
from repository.tests.RepositoryTestCase import RepositoryTestCase


class TestBZ2(RepositoryTestCase):
    """ Test Text storage """

    def setUp(self):

        super(TestBZ2, self).setUp()

        view = self.view
        cineguidePack = os.path.join(self.testdir, 'data', 'packs',
                                     'cineguide.pack')
        view.loadPack(cineguidePack)
        view.commit()

    def appended(self, compression):

        view = self.view
        khepburn = view.findPath('//CineGuide/KHepburn')
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
                view.commit()
                writer = movie.synopsis.getWriter(compression=compression,
                                                  append=True)
            else:
                break

        input.close()
        writer.close()

        self._reopenRepository()
        view = self.view

        khepburn = view.findPath('//CineGuide/KHepburn')
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
