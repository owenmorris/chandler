
__revision__  = "$Revision$"
__date__      = "$Date$"
__copyright__ = "Copyright (c) 2003-2004 Open Source Applications Foundation"
__license__   = "http://osafoundation.org/Chandler_0.1_license_terms.htm"

from repository.item.Item import Item


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
    """
    A query that returns all items of certain kinds or subkinds thereof.
    """

    def __init__(self, recursive=True):

        super(KindQuery, self).__init__()
        self.recursive = recursive

    def run(self, kinds):

        if kinds:
            matches = set()
            changedItems = set()

            for item in kinds[0].itsView._unsavedItems():
                if item._isNDirty():
                    changedItems.add(item)

            for item in self._run(kinds, changedItems):
                if item not in matches:
                    matches.add(item)
                    yield item

    def _run(self, kinds, changedItems):

        for kind in kinds:
            for item in changedItems:
                if item._kind is kind:
                    yield item

            for item in kind.itsView.queryItems(kind=kind):
                if item not in changedItems: 
                    yield item

            if self.recursive:
                subKinds = kind.getAttributeValue('subKinds', kind._references,
                                                  None, None)
                if subKinds:
                    for item in self._run(subKinds, changedItems):
                        yield item


class TextQuery(Query):

    def __init__(self, expression):

        self.expression = expression

    def run(self, repository):

        for pair in repository.searchItems(self.expression):
            yield pair
