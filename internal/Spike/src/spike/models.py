"""Observable data structures -- see ``models.txt`` for docs"""

from events import Event

__all__ = ['Set', 'SetChanged', 'Validation']


class Set(object):
    """Observable collection of unordered unique objects"""

    __slots__ = 'data','type','__weakref__'

    def __init__(self,iterable=(),type=object):
        self.data = list(iterable)
        self.type = type

    def add(self,ob):
        """Add ``ob`` to contents and generate event if new item"""
        self.replace((),(ob,))

    def remove(self,ob):
        """Remove ``ob`` from contents and generate event if it was present"""
        self.replace((ob,))

    def reset(self,iterable=()):
        """Empty the set, then add items in ``iterable``, if supplied"""
        self.replace(list(self),iterable)

    def subscribe(self,receiver,hold=False):
        """Shortcut for ``SetChanged.subscribe(set,receiver,hold)``"""
        SetChanged.subscribe(self,receiver,hold)

    def unsubscribe(self,receiver):
        """Shortcut for ``SetChanged.unsubscribe(set,receiver)``"""
        SetChanged.unsubscribe(self,receiver)

    def getReceivers(self):
        """Shortcut for ``SetChanged.getReceivers(set)``"""
        return SetChanged.getReceivers(self)

    def addValidator(self,validator,hold=False):
        """Shortcut for ``Validation.subscribe(set,validator,hold)``"""
        Validation.subscribe(self,validator,hold)

    def removeValidator(self,validator):
        """Shortcut for ``Validation.unsubscribe(set,validator)``"""
        Validation.unsubscribe(self,validator)

    def getValidators(self):
        """Shortcut for ``Validation.getReceivers(set)``"""
        return Validation.getReceivers(self)

    def replace(self,remove=(),add=()):
        """Remove items in ``remove``, add items in ``add``, generate events"""
        data = self.data
        added = []
        removed = []
        if add and self.type is not object:
            t = self.type
            for ob in add:
                if not isinstance(ob,t):
                    if t:
                        raise TypeError(
                            "%r is not of type %s" % (ob,self._typeName(t))
                        )
                    else:
                        raise TypeError("Null set cannot be changed")
        if remove:
            for ob in remove:
                if ob in data:
                    data.remove(ob)
                    removed.append(ob)
        if add:
            for ob in add:
                if ob not in data:
                    data.append(ob)
                    if ob in removed:
                        removed.remove(ob)  # ignore re-add of removed item
                    else:
                        added.append(ob)

        if removed or added:
            evt = None
            try:
                evt = Validation(self,removed,added)
                SetChanged.send(evt)    # forward event to change subscribers
            except:
                map(data.remove,added)
                map(data.append,removed)
                if evt is not None:
                    # we sent a change event, so send a rollback
                    SetChanged(self,added,removed)
                raise

    def _typeName(self,t):
        if isinstance(t,tuple):
            return '/'.join([typ.__name__ for typ in t]) or '()'
        else:
            return t.__name__

    def __repr__(self):
        r = "Set(%r)" % self.data
        if self.type is not object:
            r = r[:-1]+ (', type=%s)' % self._typeName(self.type))
        return r

    def __len__(self):
        return len(self.data)

    def __iter__(self):
        return iter(self.data)


class SetChanged(Event):
    """Set has changed membership"""

    __slots__ = 'added','removed'

    def __init__(self,sender,removed,added,**kw):
        self.removed = removed
        self.added = added
        super(SetChanged,self).__init__(sender,**kw)

    def __repr__(self):
        return "<Change for %r: removed=%r, added=%r>" % (
            self.sender, self.removed, self.added
        )


class Validation(SetChanged):
    """Validate a just-made change"""
    __slots__ = ()



