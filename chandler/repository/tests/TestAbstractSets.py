#   Copyright (c) 2003-2006 Open Source Applications Foundation
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
Test abstract sets
"""

import unittest, os

from repository.tests.RepositoryTestCase import RepositoryTestCase
from repository.tests.classes.Movie import Movie
from repository.item.Sets import Union, Intersection, Difference, Set, KindSet
from repository.item.Sets import MultiUnion, MultiIntersection


class movie(Movie):

    def __init__(self, *args, **kwds):

        super(movie, self).__init__(*args, **kwds)
        self.calls = []

    def _collectionChanged(self, op, change, name, other):

        if name != 'watches':
            self.calls.append((op, self, name, other))
        super(movie, self)._collectionChanged(op, change, name, other)
    

class TestAbstractSets(RepositoryTestCase):
    """ Test abstract sets """

    def setUp(self):

        super(TestAbstractSets, self).setUp()

        cineguidePack = os.path.join(self.testdir, 'data', 'packs',
                                     'cineguide.pack')
        view = self.rep.view
        view.loadPack(cineguidePack)
        view.commit()

        self.cineguide = view['CineGuide']
        self.movie = self.cineguide['KHepburn'].movies.first().itsKind
        self.m1 = self.cineguide['KHepburn'].movies.first()
        self.m2 = self.cineguide['m2']
        self.m3 = self.cineguide['m3']
        self.m4 = self.cineguide['m4']
        self.m5 = self.cineguide['m5']

    def testUnion(self):

        m = movie('movie', self.cineguide, self.movie)
        m.set = Union((self.m4, 'writers'), (self.m5, 'writers'))
        w = self.m4.writers.last()

        self.m4.writers.remove(w)
        self.assert_(len(m.calls) == 0)

        self.m5.writers.remove(w)
        self.assert_(len(m.calls) == 1)
        self.assert_(m.calls[0] == ('remove', m, 'set', w.itsUUID))

        del m.calls[:]
        self.m5.writers.add(w)
        self.assert_(len(m.calls) == 1)
        self.assert_(m.calls[0] == ('add', m, 'set', w.itsUUID))

        del m.calls[:]
        self.m4.writers.add(w)
        self.assert_(len(m.calls) == 0)

        self.assert_(len(list(m.set)) == 5)

    def testIntersection(self):

        m = movie('movie', self.cineguide, self.movie)
        m.set = Intersection((self.m4, 'writers'), (self.m5, 'writers'))
        w = self.m4.writers.last()

        self.m4.writers.remove(w)
        self.assert_(len(m.calls) == 1)
        self.assert_(m.calls[0] == ('remove', m, 'set', w.itsUUID))

        del m.calls[:]
        self.m5.writers.remove(w)
        self.assert_(len(m.calls) == 0)

        self.m5.writers.add(w)
        self.assert_(len(m.calls) == 0)

        self.m4.writers.add(w)
        self.assert_(len(m.calls) == 1)
        self.assert_(m.calls[0] == ('add', m, 'set', w.itsUUID))

        self.assert_(len(list(m.set)) == 1)

    def testDifference(self):

        m = movie('movie', self.cineguide, self.movie)
        m.set = Difference((self.m5, 'writers'), (self.m4, 'writers'))
        w = self.m4.writers.last()

        self.m4.writers.remove(w)
        self.assert_(len(m.calls) == 1)
        self.assert_(m.calls[0] == ('add', m, 'set', w.itsUUID))

        del m.calls[:]
        self.m5.writers.remove(w)
        self.assert_(len(m.calls) == 1)
        self.assert_(m.calls[0] == ('remove', m, 'set', w.itsUUID))

        del m.calls[:]
        self.m5.writers.add(w)
        self.assert_(len(m.calls) == 1)
        self.assert_(m.calls[0] == ('add', m, 'set', w.itsUUID))

        del m.calls[:]
        self.m4.writers.add(w)
        self.assert_(len(m.calls) == 1)
        self.assert_(m.calls[0] == ('remove', m, 'set', w.itsUUID))

        self.assert_(len(list(m.set)) == 3)

    def testItemCollection(self):

        m = movie('movie', self.cineguide, self.movie)
        m.set = Union(Difference((self.m5, 'writers'), (self.m4, 'writers')),
                      (self.m3, 'writers'))
        w = self.m4.writers.last()

        self.m4.writers.remove(w)
        self.assert_(len(m.calls) == 1)
        self.assert_(m.calls[0] == ('add', m, 'set', w.itsUUID))

        del m.calls[:]
        self.m5.writers.remove(w)
        self.assert_(len(m.calls) == 1)
        self.assert_(m.calls[0] == ('remove', m, 'set', w.itsUUID))

        del m.calls[:]
        self.m5.writers.add(w)
        self.assert_(len(m.calls) == 1)
        self.assert_(m.calls[0] == ('add', m, 'set', w.itsUUID))

        del m.calls[:]
        self.m4.writers.add(w)
        self.assert_(len(m.calls) == 1)
        self.assert_(m.calls[0] == ('remove', m, 'set', w.itsUUID))

        self.assert_(len(list(m.set)) == 6)

    def testKindSet(self):

        m = movie('movie', self.cineguide, self.movie)
        m.set = KindSet(self.m5.itsKind)
        k = self.m4.actors.first()
        count = len(list(m.set))

        l = k.movies.last()
        l.delete()

        self.assert_(len(m.calls) == 1)
        self.assert_(m.calls[0] == ('remove', m, 'set', l.itsUUID))

        del m.calls[:]
        l = self.m5.itsKind.newItem(None, self.m5.itsParent)
        self.assert_(len(m.calls) == 1)
        self.assert_(m.calls[0] == ('add', m, 'set', l.itsUUID))
        self.assert_(len(list(m.set)) == count)

    def testMultiUnion(self):

        m = movie('movie', self.cineguide, self.movie)
        m.set = MultiUnion((self.m1, 'writers'), (self.m2, 'writers'),
                           (self.m3, 'writers'), (self.m4, 'writers'),
                           (self.m5, 'writers'))
        w = self.m4.writers.last()

        self.m4.writers.remove(w)
        self.assert_(len(m.calls) == 0)

        self.m5.writers.remove(w)
        self.assert_(len(m.calls) == 1)
        self.assert_(m.calls[0] == ('remove', m, 'set', w.itsUUID))

        del m.calls[:]
        self.m5.writers.add(w)
        self.assert_(len(m.calls) == 1)
        self.assert_(m.calls[0] == ('add', m, 'set', w.itsUUID))

        del m.calls[:]
        self.m4.writers.add(w)
        self.assert_(len(m.calls) == 0)

        l = list(m.set)
        self.assert_(len(l) == 13)

        for i in xrange(0, len(l)):
            self.assert_(l.index(l[i]) == i)

    def testMultiIntersection(self):

        m = movie('movie', self.cineguide, self.movie)
        m.set = MultiIntersection((self.m1, 'writers'), (self.m2, 'writers'),
                                  (self.m3, 'writers'), (self.m4, 'writers'),
                                  (self.m5, 'writers'))
        w = self.m4.writers.last()

        self.m1.writers.add(w)
        self.assert_(len(m.calls) == 0)
        self.m2.writers.add(w)
        self.assert_(len(m.calls) == 0)
        self.m3.writers.add(w)
        self.assert_(len(m.calls) == 1)
        self.assert_(m.calls[0] == ('add', m, 'set', w.itsUUID))

        del m.calls[:]
        self.m4.writers.add(w)
        self.assert_(len(m.calls) == 0)
        self.m5.writers.add(w)
        self.assert_(len(m.calls) == 0)

        self.assert_(len(list(m.set)) == 1)

        self.m1.writers.remove(w)
        self.assert_(len(m.calls) == 1)
        self.assert_(m.calls[0] == ('remove', m, 'set', w.itsUUID))

        del m.calls[:]
        self.m2.writers.add(w)
        self.assert_(len(m.calls) == 0)
        self.m3.writers.add(w)
        self.assert_(len(m.calls) == 0)
        self.m4.writers.add(w)
        self.assert_(len(m.calls) == 0)
        self.m5.writers.add(w)
        self.assert_(len(m.calls) == 0)

    def testRefreshDelete1(self):

        m = movie('movie', self.cineguide, self.movie)
        m.set = Union((self.m4, 'writers'), (self.m5, 'writers'))
        m.set.addIndex('n', 'numeric')
        w = self.m4.writers.last().itsUUID
        size = len(m.set)
        self.assert_(w in m.set)

        view = self.rep.createView("other")
        view.findPath('//CineGuide/m4').writers.last().delete()
        view.commit()

        self.rep.view.refresh()
        self.assert_(w not in m.set)
        self.assert_(len(m.set) == size - 1)

    def testRefreshDelete2(self):

        m = movie('movie', self.cineguide, self.movie)
        w = self.m4.writers.last()
        m.set = Set(KindSet(w.itsKind))
        m.set.addIndex('n', 'numeric')
        size = len(m.set)
        self.assert_(w.itsUUID in m.set)

        view = self.rep.createView("other")
        view.findPath('//CineGuide/m4').writers.last().delete()
        view.commit()

        self.rep.view.refresh()
        self.assert_(w.itsUUID not in m.set)
        self.assert_(len(m.set) == size - 1)


if __name__ == "__main__":
#    import hotshot
#    profiler = hotshot.Profile('/tmp/TestItems.hotshot')
#    profiler.run('unittest.main()')
#    profiler.close()
    unittest.main()
