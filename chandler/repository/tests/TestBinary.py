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
Binary storage unit tests
"""

import unittest, os

from repository.tests.RepositoryTestCase import RepositoryTestCase


class TestBinary(RepositoryTestCase):
    """ Test Binary storage """

    def setUp(self):

        super(TestBinary, self).setUp()

        view = self.view
        cineguidePack = os.path.join(self.testdir, 'data', 'packs',
                                     'cineguide.pack')
        view.loadPack(cineguidePack)
        view.commit()

    def testBZ2Compressed(self):
        khepburn = self.view.findPath('//CineGuide/KHepburn')
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

        khepburn = self.view.findPath('//CineGuide/KHepburn')
        self.assert_(khepburn is not None)

        input = file(largeBinary, 'rb')
        inputStream = khepburn.picture.getInputStream()
        data = input.read()
        picture = inputStream.read()
        input.close()
        inputStream.close()

        self.assert_(data == picture)

    def testZlibCompressed(self):
        khepburn = self.view.findPath('//CineGuide/KHepburn')
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

        khepburn = self.view.findPath('//CineGuide/KHepburn')
        self.assert_(khepburn is not None)

        input = file(largeBinary, 'rb')
        inputStream = khepburn.picture.getInputStream()
        data = input.read()
        picture = inputStream.read()
        input.close()
        inputStream.close()

        self.assert_(data == picture)

    def testUncompressed(self):
        khepburn = self.view.findPath('//CineGuide/KHepburn')
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

        khepburn = self.view.findPath('//CineGuide/KHepburn')
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
