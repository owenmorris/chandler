"""Schema definition support -- see ``schema.txt`` for docs"""

__all__ = [
   'Entity', 'Role', 'Relationship', 'One', 'Many', 'NullSet', 'LoadEvent',
   'RoleActivator', 'RelationshipClass'
]

from models import Set
from events import Event
from types import ClassType
ClassTypes = type, ClassType

NullSet = Set(type=())


def load_role(cls, name):
    val = getattr(cls,name)
    if not isinstance(val,Role):
        raise AssertionError("Can't unpickle non-roles this way")
    return val

load_role.__safe_for_unpickling__ = True


class LoadEvent(Event):
    """A linkset is being created for the given role"""

    __slots__ = 'role', '_linkset'

    def __setLinkset(self,val):
        """Set new linkset on sender, copying old one's receivers if needed"""
        d = self.sender.__dict__
        try:
            ls = d[self.role]
        except KeyError:
            pass
        else:
            subscribe = val.subscribe
            for rcv in ls.getReceivers(): subscribe(rcv,True)
        d[self.role] = val
        
    linkset = property(
        lambda self: self.sender.__dict__[self.role], __setLinkset,
        doc = """Linkset to be used for the given sender and role"""
    )
       
    def __init__(self,sender,role,linkset):
        super(LoadEvent,self).__init__(sender,role=role,linkset=linkset)

    def __repr__(self):
        return "<Load event for %s of %s>" % (self.role,self.sender)


def iterTypes(typ):
    """Yield types in ``typ`` (a type or possibly-nested sequence thereof)"""
    if isinstance(typ,ClassTypes):
        yield typ
        return
    else:
        try:
            iter(typ)
        except TypeError:
            pass
        else:
            for t in typ:
                if t==typ:
                    break
                for tt in iterTypes(t):
                    yield tt
            else:
                return
    raise TypeError("%r is not a type or sequence of types" % (typ,))


class Role(object):
    """The definition of one end of a relationship type"""

    types = ()
    isReference = False
    name = owner = _inverse = None

    def __init__(self,types=(),**kw):
        self.addTypes(types)
        for k,v in kw.items():
            setattr(self,k,v)

    def __setInverse(self,inverse):
        if self._inverse is not inverse:    # No-op if no change
            if self._inverse is not None:
                raise ValueError("Role inverse cannot be changed once set")
            self._inverse = inverse
            try:
                inverse.inverse = self
            except:
                self._inverse = None    # roll back the change
                raise
            if self.owner is not None and issubclass(self.owner,Entity):
                inverse.addTypes(self.owner)

    inverse = property(
        lambda s: s._inverse, __setInverse, doc =
        """The inverse of this role"""
    )

    def addTypes(self,*types):
        """Add ``types`` to allowed types for this role"""
        types = tuple([t for t in iterTypes(types) if t not in self.types])
        refs = len([t for t in types if issubclass(t,Entity)])

        if (refs or self.isReference) and refs<>len(types):
            raise TypeError("Cannot mix entity and value types in one role")
        if len(self.types+types)>1:
            raise TypeError("Multiple value types not allowed in one role")
        if refs:
            self.isReference = True
        self.types += types

    def activateInClass(self,cls,name):
        """Role was defined/used in class `cls` under name `name`"""
        if self.owner is None:
            self.owner = cls
            self.name = name
        if issubclass(cls,Entity) and self.inverse is not None:
            self.inverse.addTypes(cls)

    def of(self,ob):
        """Return linkset for `ob` and this role"""
        if self.inverse is not None and not isinstance(ob,self.inverse.types):
            return NullSet
        try:
            d = ob.__dict__
        except AttributeError:
            return NullSet
        try:
            return d[self]
        except KeyError:           
            LoadEvent(ob,self,self.newSet(ob))
            return d[self]

    def newSet(self,ob):
        """Return new default linkset for ``ob``"""
        if self.types:
            s = Set(type=self.types)
            if self.inverse is not None:
                def maintainInverse(event):
                    for other in event.removed:
                        self.inverse.of(other).remove(ob)
                    for other in event.added:
                        self.inverse.of(other).add(ob)
                s.subscribe(maintainInverse, hold=True)
            return s
        raise TypeError("No types defined for " + repr(self))

    def __repr__(self):
        if self.name and self.owner:
            return "<Role %s of %s>" % (self.name,self.owner)
        return object.__repr__(self)

    def __reduce_ex__(self,proto=0):
        if self.owner is not None:
            return load_role, (self.owner, self.name)
        return object.__reduce_ex__(self,proto)


NOT_GIVEN = object()

class One(Role):
    """Single-valued role attribute"""

    default = compute = NOT_GIVEN

    def newSet(self,ob):
        """Return new default linkset for ``ob``

        The linkset is the same as for ``Role``, but with a subscription that
        prevents it from ever having more than one item in it.
        """
        s = super(One,self).newSet(ob)
        if self.compute is NOT_GIVEN:
            if self.default is not NOT_GIVEN:
                s.add(self.default)
        else:
            s.add(self.compute(ob))

        s.subscribe(self.__limitMembers, True)
        return s

    def __limitMembers(self,event):
        if len(event.sender)>1:
            raise ValueError("%r is singular" % self)

    def __set__(self,ob,value):
        self.of(ob).reset((value,))

    def __delete__(self,ob):
        self.of(ob).reset()

    def __get__(self,ob,typ):
        if ob is None:
            return self
        value = self.of(ob)
        if value:
            return iter(value).next()
        raise AttributeError(self.name or "???")


class Many(Role):
    """Multi-valued role attribute"""

    def __get__(self,ob,typ):
        if ob is None:
            return self
        return self.of(ob)

    def __set__(self,ob,value):
        self.of(ob).reset(value)

    def __delete__(self,ob):
        self.of(ob).reset()


class RoleActivator(type):
    """Metaclass that activates contained roles"""

    def __init__(cls,name,bases,cdict):
        for name,ob in cdict.items():
            if isinstance(ob,Role):
                ob.activateInClass(cls,name)


class Entity(object):
    """Required base class for all entity types"""

    __metaclass__ = RoleActivator

    def __init__(self,**kw):
        for k,v in kw.items():
            setattr(self,k,v)


class RelationshipClass(RoleActivator):
    """Metaclass for relationships"""

    def __init__(cls,name,bases,cdict):
        super(RelationshipClass,cls).__init__(name,bases,cdict)
        try:
            Relationship
        except NameError:
            pass
        else:
            if bases<>(Relationship,):
                raise TypeError("Relationships cannot be subclassed")
            roles = [ob for ob in cdict.values() if isinstance(ob,Role)]
            if len(roles)<>2:
                raise ValueError("Relationship must have exactly two roles")
            roles[0].inverse = roles[1]


class Relationship:
    """Subclass this to create a relationship between two roles"""
    __metaclass__ = RelationshipClass


