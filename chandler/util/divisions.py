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


# algorithm for finding groups in sorted data

def get_divisions(l, key=None):
    """
    In a list of values, find the "transition points" - the indexes in
    the array where the values are not the same from one element
    to the next.

    i.e. in a list like
    [1, 1, 1, 2, 2, 3, 3, 4, 4, 4]
    return
    [0, 3, 5, 7] because those are the indexes of the first 1,2,3, and 4

    You can use the key parameter to use another function to determine
    the value to be used in the comparison. key() will only be called
    once per value in the list.
    """

    # a description of the algorithm: use division_stack to keep
    # track of the candidate ranges which contain a "transition
    # point". The array MUST be sorted, so that for some n>m,
    # if l[n] == l[m], then l[n+1] == l[n]

    # a transition point is a place where the values "transition" from
    # one to another. For instance, in the list [2,2,2,2,2,3,3], the
    # first occurrence of "3" is a transition point with index 5.

    # Here is an example: if (4, 10) is on the stack, then we are 
    # certain that there is a transition point between 4 and 10

    # each time through the loop, we'll pop the last range off the
    # stack and search its sub-ranges.

    # For instance when we pop (4,10) off the stack, we'll need to
    # look at (4, 7) and (7, 10). If l[4] == l[7] then we can infer
    # that l[4:8] are all identical and that range doesn't contain a
    # transition. As a result, we don't put that on the stack at all.

    # if l[7] != l[10] then we know there is a transition
    # in there somewhere, and we'll put that on the stack.

    # eventually we might end up looking at (7,8) - since they're on
    # the stack, we know they must be different, so there must be a
    # transition point at 8.

    # key() is potentially expensive and people don't often run with -O,
    # so only uncomment the following line for testing!
    
    # assert sorted(l, key=key) == l, "Must start with a sorted list!"

    # division_stack and divisions always start in this ready state,
    # because if all values of the array are identical, we need to
    # indicate that the start of the array is a transition point
    division_stack = [(0,len(l)-1)]
    divisions = [0]

    # optimize for when you have/don't have a key() method
    if key is None:
        def get_value(k):
            return k
    else:
        value_cache = {}
        def get_value(k):
            """
            memoize the results of calling key() because it is
            potentially VERY expensive
            """
            # can't use get() because we're trying to avoid calls to key()
            if value_cache.has_key(k):
                result = value_cache[k]
            else:
                value_cache[k] = result = key(k)
            return result
                
    def try_division(i,j):
        assert i <= j, "%s > %s - confused" % (i,j)

        if get_value(l[i]) != get_value(l[j]):

            if j-i == 1:
                # if these two ranges are right next to each other,
                # then j must be the first occurrence of the new value
                divisions.append(j)
            else:
                # Since they are far apart, we should search this range
                division_stack.append((i,j))

    # this saves time
    if len(l) == 0:
        return []
    
    # the meat of it - the binary search
    while len(division_stack) != 0:

        # pop the next range off the stack
        index1, index2 = division_stack.pop()

        # try the middle of this range
        middle = index1 + (index2-index1)/2

        # search each of those divisions.
        # these may have the side effect of putting
        # new ranges on the stack
        try_division(index1, middle)
        try_division(middle, index2)

    return sorted(divisions)
