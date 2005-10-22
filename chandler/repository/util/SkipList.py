
__revision__  = "$Revision$"
__date__      = "$Date$"
__copyright__ = "Copyright (c) 2004 Open Source Applications Foundation"
__license__   = "http://osafoundation.org/Chandler_0.1_license_terms.htm"

from chandlerdb.util.c import CSkipList, CNode, CPoint
from random import random


class SkipList(CSkipList):
    """
    An implementation of a double-linked skip list backed by a map.

    This class is semi-abstract, its backing map is external and provided by
    callers or subclasses. The backing map is managed by the skip list and
    stores its nodes.

    Based on U{Skip Lists: a Probabilistic Alternative to Balanced
    Trees<ftp://ftp.cs.umd.edu/pub/skipLists/skiplists.pdf>},
    I{Communications of the ACM}, 33(6):668--676, June 1990, by William Pugh.
    """

    def _place(self, op, key, afterKey=None):

        map = self.map
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

            if level > self.level:
                for i in xrange(self.level, level):
                    self._head._levels.append(CPoint(len(map)))
                    self._tail._levels.append(CPoint(0))
            curr = CNode(level)
            map[key] = curr
            prevKey = None

        else:
            if op == SkipList.INSERT:
                op = SkipList.MOVE
            elif op == SkipList.REMOVE:
                del map[key]
            elif op != SkipList.MOVE:
                raise ValueError, op

            level = len(curr)
            prevKey = curr[1].prevKey

        dist = 0
        for lvl in xrange(1, self.level + 1):
            if lvl <= level:
                point = curr[lvl]
                currDist = point.dist
                prevKey = point.prevKey
                nextKey = point.nextKey
            
                if prevKey is not None:
                    prev = map[prevKey]
                    self.map._keyChanged(prevKey)
                elif op != SkipList.INSERT:
                    prev = self._head
                else:
                    prev = None

                if nextKey is not None:
                    next = map[nextKey]
                    self.map._keyChanged(nextKey)
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
                        self.map._keyChanged(afterKey)
                    else:
                        after = self._head
                    afterPoint = after[lvl]
                    afterNextKey = afterPoint.nextKey
                    afterDist = afterPoint.dist
            
                    if afterNextKey is not None:
                        map[afterNextKey].setPrev(lvl, key, afterNextKey, self)
                        self.map._keyChanged(afterNextKey)

                    after.setNext(lvl, key, afterKey, self,
                                  -afterDist + dist + 1)

                    curr.setPrev(lvl, afterKey, key, self)
                    curr.setNext(lvl, afterNextKey, key, self,
                                 -currDist + afterDist - dist)
                    self.map._keyChanged(key)

            else:
                if prevKey is not None:
                    map[prevKey][lvl].dist -= 1
                    self.map._keyChanged(prevKey)
                elif op != SkipList.INSERT:
                    self._head[lvl].dist -= 1

                if op != SkipList.REMOVE:
                    if afterKey is not None:
                        map[afterKey][lvl].dist += 1
                        self.map._keyChanged(afterKey)
                    else:
                        self._head[lvl].dist += 1
                
            while prevKey is not None:
                prev = map[prevKey]
                if len(prev) == lvl:
                    prevKey = prev[lvl].prevKey
                else:
                    break

            while afterKey is not None:
                after = map[afterKey]
                if len(after) == lvl:
                    afterKey = after[lvl].prevKey
                    if lvl < level:
                        if afterKey is None:
                            dist += self._head[lvl].dist
                        else:
                            dist += map[afterKey][lvl].dist
                else:
                    break

    def insert(self, key, afterKey):
        """
        Insert a key into the skip list.

        If C{key} is in C{map}, C{key} is moved instead.

        @param key: the key to insert
        @type key: any hashable type
        @param afterKey: the key to precede the key being inserted or
        C{None} to insert C{key} into first position
        @type afterKey: any hashable type
        """

        self._place(SkipList.INSERT, key, afterKey)

    def move(self, key, afterKey):
        """
        Move a key in the skip list.

        If C{key} is not in C{map}, C{key} is inserted instead.

        @param key: the key to move
        @type key: any hashable type
        @param afterKey: the key to precede the key being move or
        C{None} to move C{key} into first position
        @type afterKey: any hashable type
        """

        self._place(SkipList.MOVE, key, afterKey)

    def remove(self, key):
        """
        Remove a key from the skip list.

        If C{key} is not in C{map}, C{KeyError} is raised.

        @param key: the key to remove
        @type key: any hashable type
        """

        self._place(SkipList.REMOVE, key)

    def first(self, level=1):
        """
        Get the first element in the skip list.

        By specifying C{level}, the first element for the level is
        returned. For more information about skip list levels, see U{Skip
        Lists: a Probabilistic Alternative to Balanced
        Trees<ftp://ftp.cs.umd.edu/pub/skipLists/skiplists.pdf>}.

        @param level: an optional level
        @type level: int
        @return: a key
        """

        return self._head[level].nextKey

    def next(self, key, level=1):
        """
        Get the next element in the skip list relative to a given key.

        By specifying C{level}, the next element for the level is
        returned. For more information about skip list levels, see U{Skip
        Lists: a Probabilistic Alternative to Balanced
        Trees<ftp://ftp.cs.umd.edu/pub/skipLists/skiplists.pdf>}.

        @param key: the key preceeding the key being sought
        @type key: any hashable type
        @param level: an optional level
        @type level: int
        @return: a key or C{None} if C{key} is last in the skip list
        """

        return self.map[key][level].nextKey

    def previous(self, key, level=1):
        """
        Get the previous element in the skip list relative to a given key.

        By specifying C{level}, the previous element for the level is
        returned. For more information about skip list levels, see U{Skip
        Lists: a Probabilistic Alternative to Balanced
        Trees<ftp://ftp.cs.umd.edu/pub/skipLists/skiplists.pdf>}.

        @param key: the key following the key being sought
        @type key: any hashable type
        @param level: an optional level
        @type level: int
        @return: a key or C{None} if C{key} is first in the skip list
        """

        return self.map[key][level].prevKey
            
    def last(self, level=1):
        """
        Get the last element in the skip list.

        By specifying C{level}, the last element for the level is
        returned. For more information about skip list levels, see U{Skip
        Lists: a Probabilistic Alternative to Balanced
        Trees<ftp://ftp.cs.umd.edu/pub/skipLists/skiplists.pdf>}.

        @param level: an optional level
        @type level: int
        @return: a key
        """

        return self._tail[level].prevKey


    MAXLEVEL = 16       # from 1 to 16
    P        = 0.25     # 1/P is 4
    INSERT   = 0x0001
    MOVE     = 0x0002
    REMOVE   = 0x0004
