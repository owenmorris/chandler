
__revision__  = "$Revision$"
__date__      = "$Date$"
__copyright__ = "Copyright (c) 2003-2004 Open Source Applications Foundation"
__license__   = "http://osafoundation.org/Chandler_0.1_license_terms.htm"

from unittest import TestCase, main
from random import shuffle, randint

from repository.util.SkipList import SkipList

class TestSkipList(TestCase):
    """
    Skip list unit tests
    """

    def testAdd(self):
        """
        Verify that a skip list with ordered numeric keys starting from 0
        simply adds up such that key + distance == nextKey.
        """
        
        sl, map = self._fill(1000)
        
        for level in xrange(1, sl.getLevel() + 1):
            key = sl._head.getPoint(level).nextKey
            while key is not None:
                point = map[key].getPoint(level)
                if point.nextKey is not None:
                    if key + point.dist != point.nextKey:
                        raise ValueError, "%d+%d" %(key, point.dist)
                else:
                    if key + point.dist != len(map) - 1:
                        raise ValueError, "%d+%d" %(key, point.dist)
                
                key = point.nextKey

    def testShuffle(self):
        """
        Shuffle a skip list 25 times, walking each level verifying that the
        distances add up to the list's element count and stepping through
        each level verifying that the distances to the next keys are
        correct.
        """

        sl, map = self._fill(250)

        for n in xrange(0, 25):
            keys = map.keys()

            self._shuffle(keys, sl, map)
            self._walk(sl, map)
            self._step(sl, map)

    def testRemove(self):

        sl, map = self._fill(500)

        for n in xrange(0, 25):
            keys = map.keys()
            self._shuffle(keys, sl, map)

            for i in xrange(0, 10):
                sl.remove(map, keys.pop())

            self._walk(sl, map)
            self._step(sl, map)

        self.assert_(len(map) == 250)

    def testThrash(self):

        count = 500
        sl, map = self._fill(count)
    
        for i in xrange(0, 25):
            print i

            keys = map.keys()
            self._shuffle(keys, sl, map)

            r = randint(0, len(keys))
            print 'removing', r, 'elements'
            for j in xrange(0, r):
                sl.remove(map, keys.pop())

            r = randint(0, 500)
            print 'inserting', r, 'elements'
            max = len(keys) - 1
            if max >= 0:
                for j in xrange(0, r):
                    sl.insert(map, count, keys[randint(0, max)])
                    count += 1
            else:
                for j in xrange(0, r):
                    sl.insert(map, count, None)
                    count += 1
        
            self._walk(sl, map)
            self._step(sl, map)

    def _fill(self, count):

        p = None
        sl = SkipList()
        map = {}
        
        for i in xrange(0, count):
            sl.insert(map, i, p)
            p = i

        return (sl, map)

    def _shuffle(self, keys, sl, map):
        
        shuffle(keys)
        prev = None
        for key in keys:
            sl.move(map, key, prev)
            prev = key

    def _walk(self, sl, map):
        
        for lvl in xrange(1, sl.getLevel() + 1):
            node = sl._head
            point = node.getPoint(lvl)
            key = None
            d = -1
            while node is not sl._tail:
                d += point.dist
                nextKey = point.nextKey
                if nextKey is not None:
                    node = map[nextKey]
                else:
                    node = sl._tail

                point = node.getPoint(lvl)
                if key is not point.prevKey:
                    raise ValueError, "level %d key %d" %(lvl, key)
                key = nextKey

            if d + 1 != len(map):
                raise ValueError, 'incorrect length %d' %(d + 1)

    def _step(self, sl, map):

        for lvl in xrange(1, sl.getLevel() + 1):
            node = sl._head
            point = node.getPoint(lvl)
            key = None

            while node is not sl._tail:
                nextKey = point.nextKey
                step = node

                stepKey = None
                for i in xrange(0, point.dist):
                    stepKey = step.getPoint(1).nextKey
                    step = map[stepKey]

                if nextKey is not None:
                    node = map[nextKey]
                else:
                    node = sl._tail

                if step is not node:
                    if node is sl._tail:
                        prevKey = node.getPoint(1).prevKey
                        if prevKey is not None and step is not map[prevKey]:
                            raise ValueError, "level %d key %d" %(lvl, key)
                    else:
                        raise ValueError, "level %d key %d" %(lvl, key)

                point = node.getPoint(lvl)
                key = nextKey


if __name__ == "__main__":
#    import hotshot
#    profiler = hotshot.Profile('/tmp/TestItems.hotshot')
#    profiler.run('unittest.main()')
#    profiler.close()
    main()
