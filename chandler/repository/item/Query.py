
__revision__  = "$Revision$"
__date__      = "$Date$"
__copyright__ = "Copyright (c) 2002 Open Source Applications Foundation"
__license__   = "http://osafoundation.org/Chandler_0.1_license_terms.htm"


class Query(object):
    'The root class for all queries.'
    
    def __init__(self, filter):

        super(Query, self).__init__()

        self.filter = filter
        self.code = compile(filter, filter, 'eval')

    def run(self, items):

        locals = {}

        for item in items:
            locals['x'] = item
            if eval(self.code, {}, locals):
                yield item
