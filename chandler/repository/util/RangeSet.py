#   Copyright (c) 2005-2007 Open Source Applications Foundation
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


import bisect

class RangeSet(object):
    """
    Implement a set of indexes as a array of contiguous non-oveerlapping
    ranges. RangeSet is useful for storing the selected items in a
    Set, typically either a ref collection or an index.
    
    This code is particularily prone to special cases and off by one
    bugs. If you make any changes to it make sure you run the Monte
    Carlo simulations (see Test below) for a few 100 million iterations
    to convince yourself that the odds of a bug are essentially zero.
    """
    
    def __init__(self, ranges=None):

        if ranges:
            self.ranges = list(ranges)
            assert self.rangesAreValid()
        else:
            self.ranges = []

    def onInsert(self, key, position):

        self.insertOrDeleteRange(position, 1)

    def onRemove(self, key, position):

        self.insertOrDeleteRange(position, -1)

    def _getRange (self, range):
        # Private method. selectRange and unSelectRange only accepts
        # ranges of an int, a long, or a tuple of length 2 of int.
        rangeType = type (range)
        assert (rangeType in (int, long) or
                (rangeType == tuple and len (range) == 2) and
                type (range[0]) is int and type(range[1]) is int)

        if rangeType is int:
            range = (range, range)
        elif rangeType is long:
            range = (int(range), int(range))

        if range[0] < 0 or range[1] < 0:
            # Support negative array indexing like Python
            leftEdge = range [0]
            if leftEdge < 0:
                leftEdge += len (self.ranges)
                assert leftEdge > 0
            rightEdge = range [1]
            if rightEdge < 0:
                rightEdge += len (self.ranges)
                assert rightEdge > 0
            range = (leftEdge, rightEdge)
        # Negative ranges are not supported
        assert range[0] <= range[1]
        return range
            
    def _getLeftAndRightRanges (self, range):
        # Private routine for selectRange and unSelectRange.

        insertIndex = bisect.bisect_right (self.ranges, range)
        
        # Find the last range; fake one if there isn't one.
        if insertIndex > 0:
            leftRange = self.ranges [insertIndex - 1]
        else:
            leftRange = (-2, -2)

        # Find the next range; fake one if there isn't one.
        rangesLength = len (self.ranges)
        if insertIndex < rangesLength:
            rightRange = self.ranges [insertIndex]
        else:
            end = range [1]
            if rangesLength > 0:
                rangeSetEnd = self.ranges [rangesLength - 1][1]
                if rangeSetEnd > end:
                    end = rangeSetEnd
            end = end + 2
            rightRange = (end, end)
        return leftRange, rightRange, insertIndex

    def firstSelectedIndex (self):
        if len (self.ranges) == 0:
            return None
        else:
            return self.ranges[0][0]

    def isSelected (self, range):
        # Return True if the range is selected. The range maybe either
        # a tuple of integers or a single integer index. If this ends
        # up being too slow for for the integer case it could be optimized
        rangesLength = len (self.ranges)
        if rangesLength > 0:
            range = self._getRange (range)
            # Get the index to the left range
            leftRangeIndex = bisect.bisect_right (self.ranges, (range [0], self.ranges[rangesLength - 1][1]))
            if leftRangeIndex > 0:
                leftRange = self.ranges [leftRangeIndex - 1]
                if range[0] >= leftRange[0] and range[1] <= leftRange[1]:
                    return True
        return False

    def selectRange (self, range):
        # Select a range of indexes. The range maybe either
        # a tuple of integers or a single integer index.
        # This code is tricky, but efficient, because
        # ranges sare stored as a run of ranges -- DJA

        def combineRanges (startingIndex):
            # Combine ranges starting with the beginning of the one at
            # ranges[startingIndex] and ending with the one at range [1]

            endSelect = range[1]
            endingIndex = bisect.bisect_right (self.ranges, (endSelect, 0))
            # If endSelect doesn't abut the range at endingIndex then
            rangesLength = len (self.ranges)
            if (endingIndex < rangesLength and
                endSelect + 1 < self.ranges [endingIndex][0]):
                endingIndex = endingIndex - 1
            # Find the new startSelect and endSelect for the rznge
            if endingIndex < rangesLength:
                oldEndSelect = self.ranges [endingIndex][1]
            else:
                oldEndSelect = self.ranges [endingIndex - 1][1]
            if oldEndSelect > endSelect:
                endSelect = oldEndSelect
            startSelect = self.ranges [startingIndex][0]
            self.ranges [startingIndex:endingIndex + 1] = [(startSelect, endSelect)]

        range = self._getRange (range)
        leftRange, rightRange, insertIndex = self._getLeftAndRightRanges (range)
        if range[0] - 1 <= leftRange[1]:
            # Range overlaps last range
            if range[1] + 1 < rightRange[0]:
                if range[1] > leftRange[1]:
                    # Range overlaps leftRange but not rightRange. Extend leftRange
                    self.ranges [insertIndex - 1] = (leftRange[0], range[1])
            else:
                # Range overlaps leftRange and rightRange. Combine ranges
                combineRanges (insertIndex - 1)
        elif range[1] + 1 >= rightRange[0]:
            # Range overlaps next range. Extend rightRange
            self.ranges [insertIndex] = (range[0], rightRange[1])
            if range[1] > rightRange[1]:
                # Range extends beyond rightRange. Combine ranges
                combineRanges (insertIndex)
                
        else:
            # No range overlap and not already selected. Insert new range
            self.ranges.insert (insertIndex, range)

    def unSelectRange (self, range):
        # Unselect a range of indexes. The range maybe either
        # a tuple of integers or a single integer index.

        range = self._getRange (range)
        leftRange, rightRange, insertIndex = self._getLeftAndRightRanges (range)

        if range[0] <= leftRange[1]:
            # Range overlaps with last range
            if range [0] > leftRange[0]:
                # Range doesn't start at beginning of last range
                if range[1] < leftRange[1]:
                    # Range splits leftRange in two
                    self.ranges[insertIndex - 1:insertIndex] = [
                        (leftRange[0], range[0] - 1),
                        (range[1] + 1, leftRange[1])]
                else:
                    # Range overlaps later part of leftRange. Shorten leftRange
                    self.ranges [insertIndex - 1] = (leftRange[0], range[0] - 1)
            else:
                # Range starts at last range and continues beyond it
                assert range[0] == leftRange[0] and range[1] >= leftRange[1]
                # backup one range
                rightRange = leftRange
                insertIndex = insertIndex - 1

        if range[1] >= rightRange[0]:
            # New range overlaps rightRange
            if range[1] < rightRange[1]:
                # but only part of rightRange
                self.ranges [insertIndex] = (range[1] + 1, rightRange[1])
            else:
                # Collapse some ranges. Find the last range in the ranges
                # that is affected by range.
                endingIndex = bisect.bisect_right (self.ranges, (range[1], range[1]))
                if range[1] < self.ranges [endingIndex - 1][1]:
                    endingIndex = endingIndex - 1
                assert insertIndex < endingIndex
                # Remove affected ranges
                self.ranges [insertIndex:endingIndex] = []
                if insertIndex < len (self.ranges):
                    rightRange = self.ranges [insertIndex]
                    # If we overlap the rightRange then patch it up
                    if range[1] >= rightRange[0]:
                        self.ranges [insertIndex] = (range[1] + 1, rightRange[1])

    def insertOrDeleteRange (self, itemIndex, elementCount):
        # At itemIndex in the ranges, insert elementCount unselected
        # items. If elementCount is negative then count items are removed
        # starting at itemIndex. 

        rangesLength = len (self.ranges)
        if elementCount != 0 and rangesLength > 0:
            lastIndex = self.ranges[rangesLength - 1][1]
            if itemIndex <= lastIndex:
                # We have some work to do.
                if elementCount > 0:
                    # Inserting items

                    leftRange, rightRange, leftIndex = self._getLeftAndRightRanges ((itemIndex, 0))
                    if itemIndex > leftRange[0] and itemIndex <= leftRange[1]:
                        # Split range into two
                        self.ranges [leftIndex - 1:leftIndex] = [
                            (leftRange[0], itemIndex - 1),
                            (itemIndex, leftRange[1])]
                    elif leftIndex > 0:
                        leftIndex = leftIndex - 1

                else:
                    # Deleting items
                    end = itemIndex - elementCount - 1
                    if end > lastIndex:
                        elementCount = elementCount + (end - lastIndex)
                        end = lastIndex
                    range = (itemIndex, end)
                    leftIndex = 0
                    if range[1] >= self.ranges[leftIndex][0]:
                        # We're deleting indexes after the start of the ranges

                        # leftRange is the first range affected by the delete
                        leftRange, rightRange, leftIndex = self._getLeftAndRightRanges (range)
                        if leftIndex > 0:
                            leftIndex = leftIndex - 1

                        if ((range[0] == leftRange[0] and range[1] >= leftRange[1]) or
                            (range[0] - 1 <= leftRange[1] and range[1] + 1 >= rightRange[0]) or
                            range[1] >= rightRange[1]):
                            # We need to remove some ranges
                            if leftIndex == rangesLength:
                                self.ranges = []
                            else:
                                rightIndex = bisect.bisect_right (self.ranges, (range[1], 0))
                                # If range abuts rightRange then move right one forward
                                if (rightIndex < len (self.ranges) and
                                     range[1] + 1 >= self.ranges [rightIndex][0]):
                                    rightRange = self.ranges [rightIndex]
                                    rightIndex = rightIndex + 1
                                else:
                                    rightRange = self.ranges [rightIndex - 1]
                                    if range[1] >= rightRange[1]:
                                        rightRange = leftRange
                                rightEdge = rightRange[1]

                                if range[0] - 1 > leftRange [1]:
                                    # Range doesn't overlap leftRange
                                    if range[1] > rightRange[0]:
                                        leftEdge = range[1] + 1
                                    else:
                                        leftEdge = rightRange[0]
                                    if leftRange[1] >= 0:
                                        leftIndex = leftIndex + 1
                                else:
                                    leftEdge = leftRange[0]
                                
                                assert leftIndex < rightIndex
                                
                                if leftEdge >= range[0] and rightEdge <= range[1]:
                                    # The new range we calculated is inside the range that is removed
                                    del self.ranges[leftIndex:rightIndex]
                                else:
                                    self.ranges[leftIndex:rightIndex] = [(leftEdge, rightEdge)]

                # Shuffle the ranges down. There is a possible optimization here. Only the first
                # range needs to be checked for the an edge that is to the left of itemIndex.
                # So for a large number of ranges you could eliminate two comparisons per range
                for index in xrange (leftIndex, len (self.ranges)):
                    (leftEdge, rightEdge) = self.ranges[index]
                    if leftEdge >= itemIndex:
                        leftEdge = leftEdge + elementCount
                        if leftEdge < itemIndex:
                            leftEdge = itemIndex
                    if rightEdge >= itemIndex:
                        rightEdge = rightEdge + elementCount
                        if rightEdge < itemIndex:
                            rightEdge = itemIndex - 1
                    self.ranges[index] = (leftEdge, rightEdge)

    if __debug__:
        def rangesAreValid (self):
            """
            Check to make sure that ranges are sorted and non overlapping
            """
            lastRangeEnd = -1
            for range in self.ranges:
                if len (range) != 2:
                    return False
    
                (start, end) = range
                if (type (start) != int or type (end) != int or
                    lastRangeEnd >= start or
                    start > end):
                    return False
    
                lastRangeEnd = end
            return True

if __debug__:
    def Test():
        """
        Implement two different alorithms for rangeSets, one out of ranges, the other with a simple
        array. Run random changes through both algorithms and compare the results as you go. I ran
        this for a few hundred million changes and found no differences, so we have a high probability
        of certainty that there are no remaining bugs.
    
        If you make any changes be the algorithm sure to retest it, otherwise it will be difficult to
        avoid bugs.
        """
        import random
    
        alternateRanges = []
        rangeSet = RangeSet()
        random.seed(0)
        count = 0
    
        while True:
            if len (rangeSet.ranges) > 20:
                alternateRanges = []
                rangeSet.ranges = []
                
            rangesLength = len (alternateRanges)
            case = random.randint (0,3)
    
            if count == 3:
                pass
    
            if case == 0:
                # Insert items
                length = random.randint (0, 20)
                index = random.randint (0, rangesLength)
                alternateRanges [index:index] = [False] * length
                rangeSet.insertOrDeleteRange (index, length)
    
            elif case ==1:
                # Delete items
                length = random.randint (0, 20)
                index = random.randint (0, rangesLength)
                alternateRanges [index:index+length] = []
                rangeSet.insertOrDeleteRange (index, -length)
    
            elif case ==2:
                # Select items
                length = random.randint (1, 20)
                index = random.randint (0, rangesLength)
                amountToExtend = index + length - rangesLength
                if amountToExtend > 0:
                    alternateRanges [rangesLength:rangesLength] = [False] * amountToExtend
                alternateRanges [index:index+length] = [True] * length
                rangeSet.selectRange ((index, index + length - 1))
    
            elif case ==3:
                # unselect items
                length = random.randint (1, 20)
                index = random.randint (0, rangesLength)
                alternateRanges [index:index+length] = [False] * length
                rangeSet.unSelectRange ((index, index + length - 1))
            
            index = 0
            for range in rangeSet.ranges:
                assert index == 0 or index < range[0]
                assert range[0] <= range[1]
                for index in xrange (index, range[0]):
                    assert alternateRanges[index] == False
                for index in xrange (range[0], range[1] + 1):
                    assert alternateRanges[index] == True
                assert rangeSet.isSelected (range)
                index = index + 1
            
            index = 0
            for selected in alternateRanges:
                assert rangeSet.isSelected (index) == selected
                index = index + 1
            
            if len (rangeSet.ranges) > 0:
                index = rangeSet.ranges[-1][1] + 1
            for index in xrange (index, len(alternateRanges)):
                assert alternateRanges[index] == False
            
            assert rangeSet.rangesAreValid()

            count = count + 1
    
    if __name__== "__main__":
        Test()
