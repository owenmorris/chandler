"""Fundamental query operators and set manipulation"""

import operator

__all__ = [
    "AbstractFilter", "NotFilter", "AndFilter", "OrFilter", "expression",
]


class AbstractFilter(object):
    """Mixin for boolean algebra terms and set arithmetic"""

    __slots__ = ()

    def __contains__(self,ob):
        raise NotImplementedError("Subclass must define __contains__")

    def __invert__(self):
        return NotFilter(self)

    def __and__(self,other):
        return AndFilter(self,other)

    def __or__(self,other):
        return OrFilter(self,other)

    def __sub__(self,other):
        return self & ~other

    def conjuncts(self):
        yield self

    def disjuncts(self):
        yield self


class NotFilter(AbstractFilter):
    """Boolean 'not' operator"""

    __slots__ = 'base'

    def __init__(self,base):
        self.base = base

    def __invert__(self):
        return self.base

    def __contains__(self,ob):
        return ob not in self.base

    def __eq__(self,other):
        return isinstance(other,NotFilter) and self.base==other.base

    def __hash__(self):
        return hash(self.base)

    def conjuncts(self):
        for item in self.base.disjuncts():
            yield ~item

    def disjuncts(self):
        for item in self.base.conjuncts():
            yield ~item

    def __repr__(self):
        return "NotFilter(%r)" % (self.base,)


class MultiFilter(AbstractFilter):
    """Common setup for intersect/union classes"""

    __slots__ = 'items','flat',

    def __new__(cls,*items):
        # Remove duplicates
        items = set(items)
        if len(items)==1:
            # Handle degenerate case where item is intersected with itself
            return list(items)[0]

        return super(MultiFilter,cls).__new__(cls)

    def __init__(self,*items):
        # remove dupes, make immutable, flatten conditions
        self.items = frozenset(items)
        flatten = self._flatten
        self.flat = frozenset(
            [flat for item in self.items for flat in flatten(item)()]
        )
        # XXX should subscribe for notifications if applicable

    def __eq__(self,other):
        return isinstance(other,self.__class__) and self.flat==other.flat

    def __repr__(self):
        return "%s%r" % (self.__class__.__name__,tuple(self.items))


class AndFilter(MultiFilter):
    """Boolean 'and' filter"""

    __slots__ = ()

    _flatten = operator.attrgetter('conjuncts')

    def __contains__(self,ob):
        for item in self.flat:
            if ob not in item:
                return False
        return True

    def conjuncts(self):
        return iter(self.flat)


class OrFilter(MultiFilter):
    """Boolean 'or' filter"""

    __slots__ = ()

    _flatten = operator.attrgetter('disjuncts')

    def __contains__(self,ob):
        for item in self.flat:
            if ob in item:
                return True
        return False

    def disjuncts(self):
        return iter(self.flat)


def expression(expr,var="i"):
    """Compile a Python expression string into a filter object"""
    d = {}
    rep = 'expression(%r,%r)' % (expr,var)
    exec (
        "class Expr(AbstractFilter):\n"
        "   __slots__ = ()\n"
        "   def __repr__(self):\n"
        "       return %(rep)r\n"
        "   def __contains__(self,%(var)s):\n"
        "       return %(expr)s\n"
        % locals()
    ) in globals(), d
    return d['Expr']()


