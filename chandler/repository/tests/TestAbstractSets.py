"""
Test abstract sets
"""

__revision__  = "$Revision: 5439 $"
__date__      = "$Date: 2005-05-24 18:11:57 -0700 (Tue, 24 May 2005) $"
__copyright__ = "Copyright (c) 2003-2004 Open Source Applications Foundation"
__license__   = "http://osafoundation.org/Chandler_0.1_license_terms.htm"

import unittest, os

from repository.tests.RepositoryTestCase import RepositoryTestCase
from repository.tests.classes.Movie import Movie
from repository.item.Sets import Union, Intersection, Difference, Set

class movie(Movie):

    def __init__(self, *args, **kwds):

        super(movie, self).__init__(*args, **kwds)
        self.calls = []

    def collectionChanged(self, op, item, name, other, *args):

        self.calls.append((op, item, name, other))
    

class TestAbstractSets(RepositoryTestCase):
    """ Test abstract sets """

    def setUp(self):

        super(TestAbstractSets, self).setUp()

        cineguidePack = os.path.join(self.testdir, 'data', 'packs',
                                     'cineguide.pack')
        self.rep.loadPack(cineguidePack)
        self.rep.commit()

        self.cineguide = self.rep.view['CineGuide']
        self.movie = self.cineguide['KHepburn'].movies.first().itsKind
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
        self.assert_(m.calls[0] == ('remove', m, 'set', w))

        del m.calls[:]
        self.m5.writers.add(w)
        self.assert_(len(m.calls) == 1)
        self.assert_(m.calls[0] == ('add', m, 'set', w))

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
        self.assert_(m.calls[0] == ('remove', m, 'set', w))

        del m.calls[:]
        self.m5.writers.remove(w)
        self.assert_(len(m.calls) == 0)

        self.m5.writers.add(w)
        self.assert_(len(m.calls) == 0)

        self.m4.writers.add(w)
        self.assert_(len(m.calls) == 1)
        self.assert_(m.calls[0] == ('add', m, 'set', w))

        self.assert_(len(list(m.set)) == 1)

    def testDifference(self):

        m = movie('movie', self.cineguide, self.movie)
        m.set = Difference((self.m5, 'writers'), (self.m4, 'writers'))
        w = self.m4.writers.last()

        self.m4.writers.remove(w)
        self.assert_(len(m.calls) == 1)
        self.assert_(m.calls[0] == ('add', m, 'set', w))

        del m.calls[:]
        self.m5.writers.remove(w)
        self.assert_(len(m.calls) == 1)
        self.assert_(m.calls[0] == ('remove', m, 'set', w))

        del m.calls[:]
        self.m5.writers.add(w)
        self.assert_(len(m.calls) == 1)
        self.assert_(m.calls[0] == ('add', m, 'set', w))

        del m.calls[:]
        self.m4.writers.add(w)
        self.assert_(len(m.calls) == 1)
        self.assert_(m.calls[0] == ('remove', m, 'set', w))

        self.assert_(len(list(m.set)) == 3)

    def testItemCollection(self):

        m = movie('movie', self.cineguide, self.movie)
        m.set = Union(Difference((self.m5, 'writers'), (self.m4, 'writers')),
                      (self.m3, 'writers'))
        w = self.m4.writers.last()

        self.m4.writers.remove(w)
        self.assert_(len(m.calls) == 1)
        self.assert_(m.calls[0] == ('add', m, 'set', w))

        del m.calls[:]
        self.m5.writers.remove(w)
        self.assert_(len(m.calls) == 1)
        self.assert_(m.calls[0] == ('remove', m, 'set', w))

        del m.calls[:]
        self.m5.writers.add(w)
        self.assert_(len(m.calls) == 1)
        self.assert_(m.calls[0] == ('add', m, 'set', w))

        del m.calls[:]
        self.m4.writers.add(w)
        self.assert_(len(m.calls) == 1)
        self.assert_(m.calls[0] == ('remove', m, 'set', w))

        self.assert_(len(list(m.set)) == 6)


if __name__ == "__main__":
#    import hotshot
#    profiler = hotshot.Profile('/tmp/TestItems.hotshot')
#    profiler.run('unittest.main()')
#    profiler.close()
    unittest.main()
