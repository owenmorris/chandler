Interface = object  # XXX

class IFilter(Interface):
    """The most rudimentary kind of set - a filter over other sets"""

    def __contains__(ob):
        """Does this set contain `ob`?"""

    def __invert__():
        """Return an ``IFilter`` representing items *not* in this set/filter"""

    def __and__(filter):
        """Return the intersection of this set and `filter`"""

    def __or__(filter):
        """Return the union of this set and `filter`"""

    def __sub__(filter):
        """Return (set & ~filter)"""

    def conjuncts():
        """Yield the conjuncts of this filter, or the filter itself if none

        In essence, if a filter is some kind of "and" construct, this method
        should iterate over the and-ed filters (recusrively).  In all other
        cases, this should just yield self.
        """

    def disjuncts():
        """Yield the disjuncts of this filter, or the filter itself if none

        In essence, if a filter is some kind of "or" construct, this method
        should iterate over the or-ed filters (recursively).  In all other
        cases, this should just yield self.
        """


class IObservableSet(IFilter):
    """An observable set whose members can be iterated over and queried"""

    # Iteration/observation

    def __iter__():
        """Iterate over the members"""

    def __len__():
        """Return the number of objects in the set"""

    def subscribe(receiver,hold=False):
        """Shortcut for ``SetChanged.subscribe(set,receiver,hold)``"""

    def unsubscribe(receiver):
        """Shortcut for ``SetChanged.unsubscribe(set,receiver)``"""

    def getReceivers():
        """Shortcut for ``SetChanged.getReceivers(set)``"""

    # Query methods

    def where(filter):
        """Equivalent to __and__(filter)"""

    def groupedBy(*keys):
        """Return an ``IObservableMapping`` from `keys` to observable sets

        XXX key tuple, mapping values are ``IObservableSet``, etc.
        """

    def sortedBy(*keys):
        """Return a sequence ordered by `keys`"""


class IObservableMapping(IFilter):
    
    """A mapping; if used as a filter, membership in a key determines """

    def __getitem__(key):
        """Return the value for `key`, or raise KeyError"""

    def get(key,default=None):
        """Return the value for `key`, or else `default`"""

    def keys():
        """Return an ``IObservableSet`` of the keys"""
        
    def values():
        """Return an ``IObservableSet`` of the values"""
        
    def items():
        """Return an ``IObservableSet`` of ``(key,value)`` tuples"""


class IObservableSequence(IObservableSet):
    """A set that understands ordering"""

    def __getitem__(index):
        """Return the item at `index` or raise IndexError

        Note: this method must check whether `index` is a ``slice`` object, and
        return the appropriate slice of the sequence in that case.

        XXX Should slices be observable sub-sequences of the sequence???
        """

    def index(ob):
        """Return the index at which `ob` may be found, or raise ValueError"""
        
    
class ICollection(IObservableSet):
    """A mutable set"""

    def add(ob):
        """Add ``ob`` to contents and generate event if new item"""

    def remove(ob):
        """Remove ``ob`` from contents and generate event if it was present"""

    def reset(iterable=()):
        """Empty the set, then add items in ``iterable``, if supplied"""

    def replace(remove=(),add=()):
        """Remove items in ``remove``, add items in ``add``, generate events"""

    # Validation API
    
    def addValidator(validator,hold=False):
        """Shortcut for ``Validation.subscribe(set,validator,hold)``"""

    def removeValidator(validator):
        """Shortcut for ``Validation.unsubscribe(set,validator)``"""

    def getValidators():
        """Shortcut for ``Validation.getReceivers(set)``"""


class IMutableSequence(IObservableSequence, ICollection):
    """A mutable sequence

    XXX need sequence-specific events for order changes, maybe in the form of
    slice info
    """

    def __setitem__(index,value):
        """Set item(s) at `index` to `value`; `index` may be a slice"""

    def __delitem__(index):
        """Remove item(s) at `index`; `index` may be a slice"""

    def insert(index,value):
        """Insert `value` at `index`; short for ``seq[index:index]=[value]``"""

    def append(value):
        """Add `value` at end; short for ``seq[len(seq):]=[value]``"""

    def extend(iterable):
        """Append `iterable` contents, short for ``seq[len(seq):]=iterable``"""
   
# XXX IMutableMapping?


