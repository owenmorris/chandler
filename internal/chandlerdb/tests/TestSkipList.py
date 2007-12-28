#   Copyright (c) 2004-2006 Open Source Applications Foundation
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


from unittest import TestCase, main
from random import shuffle, randint

from chandlerdb.util.c import SkipList


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
        
        for level in xrange(1, sl.level + 1):
            key = sl._head[level].nextKey
            while key is not None:
                point = map[key][level]
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

            self._shuffle(keys, sl)
            self._walk(sl)
            self._step(sl)

    def testRemove(self):

        sl, map = self._fill(500)

        for n in xrange(0, 25):
            keys = map.keys()
            self._shuffle(keys, sl)

            for i in xrange(0, 10):
                sl.remove(keys.pop())

            self._walk(sl)
            self._step(sl)

        self.assert_(len(map) == 250)

    def testThrash(self):

        count = 500
        sl, map = self._fill(count)
    
        for i in xrange(0, 25):
            print i

            keys = map.keys()
            self._shuffle(keys, sl)

            r = randint(0, len(keys))
            print 'removing', r, 'elements'
            for j in xrange(0, r):
                sl.remove(keys.pop())

            r = randint(0, 500)
            print 'inserting', r, 'elements'
            max = len(keys) - 1
            if max >= 0:
                for j in xrange(0, r):
                    sl.insert(count, keys[randint(0, max)])
                    count += 1
            else:
                for j in xrange(0, r):
                    sl.insert(count, None)
                    count += 1
        
            self._walk(sl)
            self._step(sl)

    def _fill(self, count):

        p = None
        class _index(dict):
            def _keyChanged(self, key):
                pass

        map = _index()
        sl = SkipList(map)
        
        for i in xrange(0, count):
            sl.insert(i, p)
            p = i

        return (sl, map)

    def _shuffle(self, keys, sl):
        
        shuffle(keys)
        prev = None
        for key in keys:
            sl.move(key, prev)
            prev = key

    def _walk(self, sl):
        
        map = sl.map
        for lvl in xrange(1, sl.level + 1):
            node = sl._head
            point = node[lvl]
            key = None
            d = -1
            while node is not sl._tail:
                d += point.dist
                nextKey = point.nextKey
                if nextKey is not None:
                    node = map[nextKey]
                else:
                    node = sl._tail

                point = node[lvl]
                if key is not point.prevKey:
                    raise ValueError, "level %d key %d" %(lvl, key)
                key = nextKey

            if d + 1 != len(map):
                raise ValueError, 'incorrect length %d' %(d + 1)

    def _step(self, sl):

        map = sl.map
        for lvl in xrange(1, sl.level + 1):
            node = sl._head
            point = node[lvl]
            key = None

            while node is not sl._tail:
                nextKey = point.nextKey
                step = node

                stepKey = None
                for i in xrange(0, point.dist):
                    stepKey = step[1].nextKey
                    step = map[stepKey]

                if nextKey is not None:
                    node = map[nextKey]
                else:
                    node = sl._tail

                if step is not node:
                    if node is sl._tail:
                        prevKey = node[1].prevKey
                        if prevKey is not None and step is not map[prevKey]:
                            raise ValueError, "level %d key %d" %(lvl, key)
                    else:
                        raise ValueError, "level %d key %d" %(lvl, key)

                point = node[lvl]
                key = nextKey


if __name__ == "__main__":
#    import hotshot
#    profiler = hotshot.Profile('/tmp/TestItems.hotshot')
#    profiler.run('unittest.main()')
#    profiler.close()
    main()
