
def removeTypeError(f):
    def g(dt1, dt2):
        naive1 = (dt1.tzinfo is None)
        naive2 = (dt2.tzinfo is None)
        
        if naive1 != naive2:
            if naive1:
                dt2 = dt2.replace(tzinfo=None)
            else:
                dt1 = dt1.replace(tzinfo=None)
        return f(dt1, dt2)
    return g

__opFunctions = {
    'cmp': removeTypeError(lambda x, y: cmp(x, y)),
    'max': removeTypeError(lambda x, y: max(x, y)),
    'min': removeTypeError(lambda x, y: min(x, y)),
    '-':   removeTypeError(lambda x, y: x - y),
    '<':   removeTypeError(lambda x, y: x < y),
    '>':   removeTypeError(lambda x, y: x > y),
    '<=':  removeTypeError(lambda x, y: x <= y),
    '>=':  removeTypeError(lambda x, y: x >= y),
    '==':  removeTypeError(lambda x, y: x == y),
    '!=':  removeTypeError(lambda x, y: x != y)
}

def datetimeOp(dt1, operator, dt2):
    """
    This function is a workaround for some issues with
    comparisons of naive and non-naive C{datetimes}. Its usage
    is slightly goofy (but makes diffs easier to read):
    
    If you had in code::
    
        dt1 < dt2
        
    and you weren't sure whether dt1 and dt2 had timezones, you could
    convert this to::
    
       datetimeOp(dt1, '<', dt2)
       
    and not have to deal with the TypeError you'd get in the original code. 
   
    Similar conversions hold for other comparisons, '-', '>', '<=', '>=',
    '==', '!='. Also, there are functions with implied comparison; you can do::
   
       max(dt1, dt2) --> datetimeOp(dt1, 'max', dt2)
      
    and similarly for min, cmp.
    
    For more details (and why this is a kludge), see
    <http://wiki.osafoundation.org/bin/view/Journal/GrantBaillie20050809>
    """
    
    f = __opFunctions.get(operator, None)
    if f is None:
        raise ValueError, "Unrecognized operator '%s'" % (operator)
    return f(dt1, dt2)
    