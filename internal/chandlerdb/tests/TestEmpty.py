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
from chandlerdb.util.c import Empty


class TestEmpty(RepositoryTestCase):

    def setUp(self):
        
        super(TestEmpty, self).setUp()
        self.loadCineguide(self.view)

    def testSetOtherSide(self):

        view = self.view

        k = view.findPath('//CineGuide/KHepburn')
        m1 = k.movies.first()
        m2 = k.movies.next(m1)
        m3 = k.movies.next(m2)

        k.movies = Empty
        view.commit()

        self.assert_(k.movies is Empty)
        self.assert_(not list(k.movies))

        m1.actors = [k]
        m2.actors = [k]
        m3.actors = [k]

        self.assert_(list(k.movies) == [m1, m2, m3])

    def testDefaultValue(self):

        view = self.view

        k = view.findPath('//CineGuide/KHepburn')
        m1 = k.movies.first()
        m2 = k.movies.next(m1)
        m3 = k.movies.next(m2)

        k.itsKind.getAttribute('movies').defaultValue = Empty
        del k.movies
        view.commit()  # ref list removal may be deferred until commit

        self.assert_(not k.hasLocalAttributeValue('movies'))
        self.assert_('movies' not in k.itsRefs)
        self.assert_(k.movies is Empty)
        self.assert_(not list(k.movies))

        m1.actors = [k]
        m2.actors = [k]
        m3.actors = [k]

        self.assert_(list(k.movies) == [m1, m2, m3])


if __name__ == "__main__":
    import unittest
    unittest.main()
