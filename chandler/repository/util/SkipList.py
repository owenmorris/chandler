
__revision__  = "$Revision$"
__date__      = "$Date$"
__copyright__ = "Copyright (c) 2004 Open Source Applications Foundation"
__license__   = "http://osafoundation.org/Chandler_0.1_license_terms.htm"

from random import random


class SkipList(object):
    """
    An implementation of a double-linked skip list backed by a map.

    This class is semi-abstract, its backing map is external and provided by
    callers or subclasses. The backing map is managed by the skip list and
    stores its nodes.

    Based on U{Skip Lists: a Probabilistic Alternative to Balanced
    Trees<ftp://ftp.cs.umd.edu/pub/skipLists/skiplists.pdf>},
    I{Communications of the ACM}, 33(6):668--676, June 1990, by William Pugh.
    """

    class node(object):

        def __init__(self, level, skipList):

            self._levels = []
            for i in xrange(0, level):
                self._levels.append(skipList._createPoint(0))

            super(SkipList.node, self).__init__()

        def getLevel(self):

            return len(self._levels)

        def getPoint(self, level):

            assert level > 0
            return self._levels[level - 1]

        def setNext(self, level, nextKey, key, skipList, delta):

            if nextKey is None:
                skipList._tail.getPoint(level).prevKey = key

            point = self.getPoint(level)
            point.nextKey = nextKey
            point.dist += delta

        def setPrev(self, level, prevKey, key, skipList):

            if prevKey is None:
                skipList._head.getPoint(level).nextKey = key

            self.getPoint(level).prevKey = prevKey

    class point(object):

        def __init__(self, dist, skipList):

            self.prevKey = None
            self.nextKey = None
            self.dist = dist
            
            super(SkipList.point, self).__init__()

        def __repr__(self):

            return '<point: %s, %s, %s>' %(self.prevKey, self.nextKey,
                                           self.dist)


    def __init__(self):

        self.__init()
        super(SkipList, self).__init__()
        
    def __init(self):

        self._head = self._createNode(0)
        self._tail = self._createNode(0)

    def _createNode(self, level):

        return SkipList.node(level, self)

    def _createPoint(self, dist):

        return SkipList.point(dist, self)

    def _keyChanged(self, key):

        pass

    def getLevel(self):
        """
        Return the skip list's current level.

        See U{Skip Lists: a Probabilistic Alternative to Balanced
        Trees<ftp://ftp.cs.umd.edu/pub/skipLists/skiplists.pdf>} for more
        information.

        @return: an integer
        """

        return self._head.getLevel()

    def _place(self, map, op, key, afterKey=None):

        assert key != afterKey
        curr = map.get(key, None)

        if curr is None:
            if op == SkipList.REMOVE:
                raise KeyError, key
            elif op != SkipList.INSERT:
                op = SkipList.INSERT
            
            level = 1
            while (random() < SkipList.P and level < SkipList.MAXLEVEL):
                level += 1

            if level > self.getLevel():
                for i in xrange(self.getLevel(), level):
                    self._head._levels.append(self._createPoint(len(map)))
                    self._tail._levels.append(self._createPoint(0))
            curr = self._createNode(level)
            map[key] = curr
            prevKey = None

        else:
            if op == SkipList.INSERT:
                op = SkipList.MOVE
            elif op == SkipList.REMOVE:
                del map[key]
            elif op != SkipList.MOVE:
                raise ValueError, op

            level = curr.getLevel()
            prevKey = curr.getPoint(1).prevKey

        dist = 0
        for lvl in xrange(1, self.getLevel() + 1):
            if lvl <= level:
                point = curr.getPoint(lvl)
                currDist = point.dist
                prevKey = point.prevKey
                nextKey = point.nextKey
            
                if prevKey is not None:
                    prev = map[prevKey]
                    self._keyChanged(prevKey)
                elif op != SkipList.INSERT:
                    prev = self._head
                else:
                    prev = None

                if nextKey is not None:
                    next = map[nextKey]
                    self._keyChanged(nextKey)
                elif op != SkipList.INSERT:
                    next = self._tail
                else:
                    next = None

                if prev is not None:
                    prev.setNext(lvl, nextKey, prevKey, self, currDist - 1)
                if next is not None:
                    next.setPrev(lvl, prevKey, nextKey, self)

                if op == SkipList.REMOVE:
                    point.nextKey = None
                    point.prevKey = None
                    point.dist = 0
                else:
                    if afterKey is not None:
                        after = map[afterKey]
                        self._keyChanged(afterKey)
                    else:
                        after = self._head
                    afterPoint = after.getPoint(lvl)
                    afterNextKey = afterPoint.nextKey
                    afterDist = afterPoint.dist
            
                    if afterNextKey is not None:
                        map[afterNextKey].setPrev(lvl, key, afterNextKey, self)
                        self._keyChanged(afterNextKey)

                    after.setNext(lvl, key, afterKey, self,
                                  -afterDist + dist + 1)

                    curr.setPrev(lvl, afterKey, key, self)
                    curr.setNext(lvl, afterNextKey, key, self,
                                 -currDist + afterDist - dist)
                    self._keyChanged(key)

            else:
                if prevKey is not None:
                    map[prevKey].getPoint(lvl).dist -= 1
                    self._keyChanged(prevKey)
                elif op != SkipList.INSERT:
                    self._head.getPoint(lvl).dist -= 1

                if op != SkipList.REMOVE:
                    if afterKey is not None:
                        map[afterKey].getPoint(lvl).dist += 1
                        self._keyChanged(afterKey)
                    else:
                        self._head.getPoint(lvl).dist += 1
                
            while prevKey is not None:
                prev = map[prevKey]
                if prev.getLevel() == lvl:
                    prevKey = prev.getPoint(lvl).prevKey
                else:
                    break

            while afterKey is not None:
                after = map[afterKey]
                if after.getLevel() == lvl:
                    afterKey = after.getPoint(lvl).prevKey
                    if lvl < level:
                        if afterKey is None:
                            dist += self._head.getPoint(lvl).dist
                        else:
                            dist += map[afterKey].getPoint(lvl).dist
                else:
                    break

    def insert(self, map, key, afterKey):
        """
        Insert a key into the skip list.

        If C{key} is in C{map}, C{key} is moved instead.

        @param map: the skip list's backing map
        @type map: dict
        @param key: the key to insert
        @type key: any hashable type
        @param afterKey: the key to precede the key being inserted or
        C{None} to insert C{key} into first position
        @type afterKey: any hashable type
        """

        self._place(map, SkipList.INSERT, key, afterKey)

    def move(self, map, key, afterKey):
        """
        Move a key in the skip list.

        If C{key} is not in C{map}, C{key} is inserted instead.

        @param map: the skip list's backing map
        @type map: dict
        @param key: the key to move
        @type key: any hashable type
        @param afterKey: the key to precede the key being move or
        C{None} to move C{key} into first position
        @type afterKey: any hashable type
        """

        self._place(map, SkipList.MOVE, key, afterKey)

    def remove(self, map, key):
        """
        Remove a key from the skip list.

        If C{key} is not in C{map}, C{KeyError} is raised.

        @param map: the skip list's backing map
        @type map: dict
        @param key: the key to remove
        @type key: any hashable type
        """

        self._place(map, SkipList.REMOVE, key)

    def position(self, map, key):

        dist = -1

        curr = map[key]
        while curr is not None:
            level = curr.getLevel()
            point = curr.getPoint(level)
            if point.prevKey is None:
                dist += self._head.getPoint(level).dist
                curr = None
            else:
                curr = map[point.prevKey]
                dist += curr.getPoint(level).dist

        return dist

    def access(self, map, position):
        """
        Get the key at a given position in the skip list.

        C{position} is 0-based and may be negative to begin search from end
        going backwards with C{-1} being the index of the last element of
        the skip list.

        C{IndexError} is raised if C{position} is out of range.

        @param map: the skip list's backing map
        @type map: dict
        @param position: the position of the key sought
        @type position: int
        @return: a key
        """

        count = len(map)
        
        if position < 0:
            position += count

        if position < 0 or position >= count:
            raise IndexError, 'position out of range: %s' %(position)

        pos = -1
        node = self._head

        for lvl in xrange(self.getLevel(), 0, -1):
            while True:
                point = node.getPoint(lvl)
                nextKey = point.nextKey
                next = pos + point.dist

                if nextKey is None or next > position:
                    break
                if next == position:
                    return nextKey

                #print 'skipping to', lvl, next
                pos = next
                node = map[nextKey]

        assert False

    def first(self, map, level=1):
        """
        Get the first element in the skip list.

        By specifying C{level}, the first element for the level is
        returned. For more information about skip list levels, see U{Skip
        Lists: a Probabilistic Alternative to Balanced
        Trees<ftp://ftp.cs.umd.edu/pub/skipLists/skiplists.pdf>}.

        @param map: the skip list's backing map
        @type map: dict
        @param level: an optional level
        @type level: int
        @return: a key
        """

        return self._head.getPoint(level).nextKey

    def next(self, map, key, level=1):
        """
        Get the next element in the skip list relative to a given key.

        By specifying C{level}, the next element for the level is
        returned. For more information about skip list levels, see U{Skip
        Lists: a Probabilistic Alternative to Balanced
        Trees<ftp://ftp.cs.umd.edu/pub/skipLists/skiplists.pdf>}.

        @param map: the skip list's backing map
        @type map: dict
        @param key: the key preceeding the key being sought
        @type key: any hashable type
        @param level: an optional level
        @type level: int
        @return: a key or C{None} if C{key} is last in the skip list
        """

        return map[key].getPoint(level).nextKey

    def previous(self, map, key, level=1):
        """
        Get the previous element in the skip list relative to a given key.

        By specifying C{level}, the previous element for the level is
        returned. For more information about skip list levels, see U{Skip
        Lists: a Probabilistic Alternative to Balanced
        Trees<ftp://ftp.cs.umd.edu/pub/skipLists/skiplists.pdf>}.

        @param map: the skip list's backing map
        @type map: dict
        @param key: the key following the key being sought
        @type key: any hashable type
        @param level: an optional level
        @type level: int
        @return: a key or C{None} if C{key} is first in the skip list
        """

        return map[key].getPoint(level).prevKey
            
    def last(self, map, level=1):
        """
        Get the last element in the skip list.

        By specifying C{level}, the last element for the level is
        returned. For more information about skip list levels, see U{Skip
        Lists: a Probabilistic Alternative to Balanced
        Trees<ftp://ftp.cs.umd.edu/pub/skipLists/skiplists.pdf>}.

        @param map: the skip list's backing map
        @type map: dict
        @param level: an optional level
        @type level: int
        @return: a key
        """

        return self._tail.getPoint(level).prevKey


    MAXLEVEL = 16       # from 1 to 16
    P        = 0.25     # 1/P is 4
    INSERT   = 0x0001
    MOVE     = 0x0002
    REMOVE   = 0x0004
