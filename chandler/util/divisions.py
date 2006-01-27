

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
        assert i < j

        if get_value(l[i]) != get_value(l[j]):
            if j-i == 1:
                divisions.append(j)
            else:
                division_stack.append((i,j))
                
    while len(division_stack) != 0:
        index1, index2 = division_stack.pop()

        middle = index1 + (index2-index1)/2

        try_division(index1, middle)
        try_division(middle, index2)

    return sorted(divisions)
