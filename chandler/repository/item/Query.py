
__revision__  = "$Revision$"
__date__      = "$Date$"
__copyright__ = "Copyright (c) 2002 Open Source Applications Foundation"
__license__   = "http://osafoundation.org/Chandler_0.1_license_terms.htm"


class Query(object):
    'The root class for all queries.'

    def run(self, items):
        raise NotImplementedError, "Query.run"


class FilterQuery(Query):
    'A query that runs a python filter expression over a collection of items'
    
    def __init__(self, filter):

        super(FilterQuery, self).__init__()

        self.filter = filter
        self.code = compile(filter, filter, 'eval')

    def run(self, items):

        locals = {}

        for item in items:
            locals['x'] = item
            if eval(self.code, {}, locals):
                yield item


class KindQuery(Query):
    'A query that returns all items of certain kinds or subkind thereof'

    def __init__(self):

        super(KindQuery, self).__init__()

    def run(self, kinds):

        for kind in kinds:
            for item in kind.getAttributeValue('items', default=[]):
                if item.isNew():
                    yield item

            query = "/item[kind='%s']" %(kind.getUUID().str64())
            for item in kind.getRepository().queryItems(query):
                yield item

            subKinds = kind.getAttributeValue('subKinds', default=[])
            for item in self.run(subKinds):
                yield item
