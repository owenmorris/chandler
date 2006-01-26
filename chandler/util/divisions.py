

# algorithm for finding groups in sorted data

def get_divisions(l, key=None):
    """
    In a list of values, find the "transition points" - the indexes in
    the array where the values are not the same from one element
    to the next.

    i.e. in a list like
    [1, 1, 1, 2, 2, 3, 3, 4, 4, 4]
    return
    [0, 3, 5, 7] because those are 
    """

    division_stack = [(0,len(l)-1)]

    divisions = [0]

    # one version when there is a key, one without
    if key is None:
        def try_division(i,j):
            if l[i] != l[j]:
                if j-i == 1:
                    divisions.append(j)
                else:
                    division_stack.append((i,j))
    else:
        def try_division(i,j):
            assert i < j

            if key(l[i]) != key(l[j]):
                if j-i == 1:
                    divisions.append(j)
                else:
                    division_stack.append((i,j))

    while len(division_stack) != 0:
        index1, index2 = division_stack.pop()

        middle = index1 + (index2-index1)/2

        counter += 1                    # for middle
        try_division(index1, middle)
        try_division(middle, index2)

    return sorted(divisions)
