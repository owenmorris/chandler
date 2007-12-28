#   Copyright (c) 2004-2007 Open Source Applications Foundation
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

import os
from chandlerdb.util.RepositoryTestCase import RepositoryTestCase
                                                                                

class TestInheritFrom(RepositoryTestCase):

    def setUp(self):
        
        super(TestInheritFrom, self).setUp()
        self.loadCineguide(self.view)

    def testList(self):

        view = self.view

        k = view.findPath('//CineGuide/KHepburn')
        butlerKind = view.findPath('//Schema/CineGuide/Kinds/Butler')
        butler = butlerKind.newItem('butler', k.itsParent)
        k.inheritTo = [butler]

        movies = list(k.movies)

        # a way
        butlerMovies = list(x for x in butler.movies)
        self.failUnlessEqual(movies, butlerMovies)

        # another way
        butlerMovies = list(butler.movies)

        self.failUnlessEqual(movies, butlerMovies)


if __name__ == "__main__":
    import unittest
    unittest.main()
