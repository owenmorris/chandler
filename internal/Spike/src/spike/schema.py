"""Schema definition support -- see ``schema.txt`` for docs"""

__all__ = [
   'Entity', 'Role', 'Relationship', 'One', 'Many', 'NullSet', 'LoadEvent',
   'Enumeration', 'Activator', 'RelationshipClass', 'EnumerationClass',
   'ActiveDescriptor',
]

from models import Set
from events import Event
from types import ClassType
ClassTypes = type, ClassType

NullSet = Set(type=())


def __setUUID(self,uuid):
    """Validate a UUID and save it in self._uuid unless it's already set

    Used to create a property for roles and entity/relationship classes to
    track their UUIDs.
    """
    uustr = str(uuid).lower()
    if map(len,uustr.split('-')) == [8, 4, 4, 4, 12]:
        for c in uustr:
            if c not in '0123456789-abcdef':
                raise ValueError("%r is not valid in UUID format" % c)
        else:
            old = getattr(self,'uuid',None)
            if old is not None and old<>uustr:
                raise TypeError(
                    "Can't change UUID once set (was %s)" % old
                )
            self._uuid = uustr
            return

    raise ValueError("%r is not a valid UUID" % (uuid,))


uuid_prop = property(
    lambda self:self.__dict__.get('_uuid'),     # avoid inheritance in class!
    __setUUID,
    doc="Universally Unique identifier for this object"
)


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
            subscribe = val.addValidator
            for rcv in ls.getValidators(): subscribe(rcv,True)
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


class ActiveDescriptor(object):
    """Abstract base for descriptors needing activation by Entity classes"""

    def activateInClass(self,cls,name):
        """Redefine in subclasses to do useful things with `cls` & `name`"""
        raise NotImplementedError


class Role(ActiveDescriptor):
    """The definition of one end of a relationship type"""

    types = ()
    isReference = False
    name = owner = _inverse = _loadMap = _uuid = None
    cardinality = "Role"

    def __init__(self,types=(),**kw):
        self.addTypes(types)
        self._loadMap = {}
        for k,v in kw.items():
            setattr(self,k,v)
        self.setDoc()   # default the doc string


    def __setInverse(self,inverse):
        if self._inverse is not inverse:    # No-op if no change
            if self._inverse is not None:
                raise ValueError("Role inverse cannot be changed once set")
            self._inverse = inverse
            try:
                inverse.inverse = self
            except:
                self._setattr('_inverse',None)  # roll back the change
                raise
            if self.owner is not None and issubclass(self.owner,Entity):
                inverse.addTypes(self.owner)

    inverse = property(
        lambda s: s._inverse, __setInverse, doc =
        """The inverse of this role"""
    )

    uuid = uuid_prop

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
        self._setattr('types',self.types + types)
        self.setDoc()   # update the doc string

    def activateInClass(self,cls,name):
        """Role was defined/used in class `cls` under name `name`"""
        if self.owner is None:
            self.owner = cls
            self.name = name
        if issubclass(cls,Entity) and self.inverse is not None:
            self.inverse.addTypes(cls)

    def of(self,ob):
        """Return linkset for `ob` and this role"""
        try:
            d = ob.__dict__
        except AttributeError:
            return self.load(ob)
        else:
            try:
                return d[self]
            except KeyError:
                return self.load(ob)

    def load(self,ob):
        """Load linkset for `ob`, using registered loader or LoadEvent"""

        loadfunc = self.getLoader(ob)
        if loadfunc is not None:

            linkset = self.newSet(ob)
            newlinks = loadfunc(ob,linkset)

            if newlinks is not None and newlinks is not linkset:
                if hasattr(ob,'__dict__'):
                    ob.__dict__[self] = newlinks
                return newlinks

        elif self.inverse and not isinstance(ob,self.inverse.types):
            return NullSet
        else:
            linkset = self.newSet(ob)

        if hasattr(ob,'__dict__'):
            return LoadEvent(ob,self,linkset).linkset
        else:
            return NullSet


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

    def setLoader(self,cls,loadfunc):
        if cls in self._loadMap:
            raise KeyError("A loader is already installed in %s for %s"
                % (self,cls)
            )
        self._loadMap[cls] = loadfunc

    def loader(self,func):
        """Decorator to declare a method as a loader for this attribute"""
        return LoaderWrapper(self,func)

    def getLoader(self,ob):
        lm = self._loadMap
        for cls in ob.__class__.__mro__:
            if cls in lm:
                return lm[cls]

    def __repr__(self):
        if self.name and self.owner:
            return "<Role %s of %s>" % (self.name,self.owner)
        return object.__repr__(self)

    def __reduce_ex__(self,proto=0):
        if self.owner is not None:
            return load_role, (self.owner, self.name)
        return object.__reduce_ex__(self,proto)

    def __getDoc(self):
        return self.__dict__.get('doc')

    def __setDoc(self,val):
        self.__dict__['doc'] = val
        self.setDoc()

    doc = property(__getDoc,__setDoc)

    def __getDisplayName(self):
        return self.__dict__.get('displayName')

    def __setDisplayName(self,val):
        self.__dict__['displayName'] = val
        self.setDoc()

    displayName = property(__getDisplayName,__setDisplayName)

    def setDoc(self):
        doc = self.doc
        name = self.displayName
        if not name:
            name = self.docInfo()
        else:
            name = "%s -- %s" % (name,self.docInfo())
        if not doc:
            doc = name
        else:
            doc = "%s\n\n%s" % (name,doc)
        self._setattr('__doc__',doc)

    def docInfo(self):
        return ("%s(%s)" %
            (self.cardinality,
                '/'.join([typ.__name__ for typ in self.types]) or '()'
            )
        )

    def _setattr(self,attr,value):
        """Private routine allowing bypass of normal setattr constraints"""
        super(Role,self).__setattr__(attr,value)

    def __setattr__(self,attr,value):
        if not hasattr(type(self),attr):
            raise TypeError("%r is not a public attribute of %r objects"
                % (attr,type(self).__name__))
        old = self.__dict__.get(attr)
        if old is not None and old<>value:
            raise TypeError(
                "Role objects are immutable; can't change %r once set" % attr
            )
        self._setattr(attr,value)

NOT_GIVEN = object()

class One(Role):
    """Single-valued role attribute"""

    default = compute = NOT_GIVEN
    cardinality = "One"

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

        s.addValidator(self.__limitMembers, True)
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

    def docInfo(self):
        doc = super(One,self).docInfo()
        if self.compute is not NOT_GIVEN and hasattr(self.compute,'__name__'):
            doc = doc[:-1]+(', compute=%s' % self.compute.__name__)+doc[-1]
        elif self.default is not NOT_GIVEN:
            doc = doc[:-1]+(', default=%r' % self.default)+doc[-1]
        return doc


class Many(Role):
    """Multi-valued role attribute"""

    cardinality = "Many"

    def __get__(self,ob,typ):
        if ob is None:
            return self
        return self.of(ob)

    def __set__(self,ob,value):
        self.of(ob).reset(value)

    def __delete__(self,ob):
        self.of(ob).reset()


class Activator(type):
    """Metaclass that activates contained roles"""

    uuid = uuid_prop

    def __new__(meta,name,bases,cdict):
        # Does the class body have a 'uuid' declaration?
        uuid = cdict.get('uuid')

        if isinstance(uuid,ActiveDescriptor):
            # Looks like the class wants to define a 'uuid' role for
            # its instances, so don't confuse it with the class' missing UUID
            uuid = None

        elif uuid:
            # Strip the UUID out so instances don't end up seeing it
            del cdict['uuid']

        # Create the class
        cls = super(Activator,meta).__new__(meta,name,bases,cdict)

        if uuid:
            # and set its uuid if appropriate
            cls.uuid = uuid

        return cls

    def __init__(cls,name,bases,cdict):
        for name,ob in cdict.items():
            if isinstance(ob,ActiveDescriptor):
                ob.activateInClass(cls,name)


class Entity(object):
    """Required base class for all entity types"""

    __metaclass__ = Activator

    def __init__(self,**kw):
        for k,v in kw.items():
            setattr(self,k,v)


class RelationshipClass(Activator):
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


class EnumerationClass(Activator):
    """Metaclass for enumerations"""

    def __init__(cls,name,bases,cdict):
        super(EnumerationClass,cls).__init__(name,bases,cdict)
        try:
            Enumeration
        except NameError:
            return  # Enumeration isn't defined yet, so nothing to verify

        if bases<>(Enumeration,):
            raise TypeError("Enumerations cannot be subclassed")

        d = {}
        for k,v in cls.iteritems():
            if v in d:
                v = unicode(v)
                raise TypeError(
                    "Duplicate definitions: %s=enum(%r) and %s=enum(%r)"
                    % (d[v],v,k,v)
                )
            d[v] = k

    def __iter__(cls):
        for k,v in cls.iteritems():
            yield v

    def iteritems(cls):
        """Yield names and values of all enums in this class"""
        for k in dir(cls):
            v = getattr(cls,k)
            if isinstance(v,Enumeration):
                yield k,v


class Enumeration(unicode):
    """Base class for value types with a fixed set of possible values"""

    __metaclass__ = EnumerationClass

    def __new__(self,*args,**kw):
        raise TypeError("Enumeration instances cannot be created directly")

    @property
    def name(self):
        cls = self.__class__
        for k,v in cls.iteritems():
            if v==self:
                return k
        raise AssertionError("Invalid instance",unicode(self))

    def __repr__(self):
        return ".".join([self.__class__.__name__,self.name])


class enum(ActiveDescriptor):
    """schema.enum(displayName) -- define an enumeration value"""

    def __init__(self,displayName):
        self.displayName = displayName

    def activateInClass(self,cls,name):
        setattr(cls,name,unicode.__new__(cls,self.displayName))


class LoaderWrapper(ActiveDescriptor):
    """Registration wrapper for loader methods declared ``@aRole.loader``"""

    def __init__(self,role,func):
        self.role = role
        self.func = func

    def __repr__(self):
        return "<Loader wrapping %s for %s>" % (self.func,self.role)

    def activateInClass(self,cls,name):
        self.role.setLoader(cls,self.func)

