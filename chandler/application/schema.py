from repository.persistence.RepositoryView import NullRepositoryView
from repository.item.Item import Item as Base
from repository.schema.Kind import CDescriptor, Kind
from repository.schema.Attribute import Attribute
from repository.schema import Types
from application.Parcel import Manager, Parcel
import __main__, repository, threading, os, sys

ANONYMOUS_ROOT = "//userdata"

__all__ = [
    'ActiveDescriptor', 'Activator', 'Role', 'itemFor', 'kindInfo',
    'One', 'Many', 'Sequence', 'Mapping', 'Item', 'ItemClass',
    'importString', 'parcel_for_module', 'TypeReference', 'Enumeration'
]

all_aspects = Attribute.valueAspects + Attribute.refAspects + \
    ('displayName','description')

global_lock = threading.RLock()


class TypeReference:
    """Reference a core schema type (e.g. Integer) by its repository path"""

    def __init__(self,path):
        if nrv.findPath(path) is None:
            raise NameError("Type %r not found in the core schema" % (path,))
        self.path = path
        self.__name__ = path.split('/')[-1]

    def __repr__(self):
        return "TypeReference(%r)" % self.path

    def _create_schema_item(self):
        item = nrv.findPath(self.path)
        if item is None:
            raise TypeError("Unrecognized type", self.path)
        return item

    def _init_schema_item(self,item):
        pass


class ActiveDescriptor(object):
    """Abstract base for descriptors needing activation by their classes"""

    def activateInClass(self,cls,name):
        """Redefine in subclasses to do useful things with `cls` & `name`"""
        raise NotImplementedError


class Activator(type):
    """Metaclass that activates contained ``ActiveDescriptor`` instances"""

    def __init__(cls,name,bases,cdict):
        for name,ob in cdict.items():
            if isinstance(ob,ActiveDescriptor):
                ob.activateInClass(cls,name)


class Role(ActiveDescriptor,CDescriptor):
    """Descriptor for a schema-defined attribute"""

    owner = type = _inverse = None

    __slots__ = ['__dict__']
    __slots__.extend(all_aspects)

    def __new__(cls, type=None, **kw):
        return super(Role,cls).__new__(cls,kw.get('name'))

    def __init__(self,type=None,**kw):
        super(Role,self).__init__(kw.get('name'))
        if type is not None:
            self.type = type
        for k,v in kw.items():
            if k!='name':   # XXX workaround CDescriptor not allowing name set
                setattr(self,k,v)
        self.setDoc()   # default the doc string

    def activateInClass(self,cls,name):
        """Role was defined/used in class `cls` under name `name`"""
        if self.owner is None:
            self.owner = cls
            CDescriptor.__init__(self,name)
        if issubclass(cls,Item) and self.inverse is not None:
            self.inverse.type = cls

    def _setattr(self,attr,value):
        """Private routine allowing bypass of normal setattr constraints"""
        super(Role,self).__setattr__(attr,value)

    def __setattr__(self,attr,value):
        if '_schema_attr_' in self.__dict__:
            raise TypeError(
                "Role object cannot be modified after use"
            )
        if not hasattr(type(self),attr):
            raise TypeError("%r is not a public attribute of %r objects"
                % (attr,type(self).__name__))
        old = self.__dict__.get(attr)
        if old is not None and old<>value:
            raise TypeError(
                "Role objects are immutable; can't change %r once set" % attr
            )

        self._setattr(attr,value)
        if attr=='type' and value is not None:
            if not hasattr(value,"_create_schema_item"):
                self._setattr(attr,old) # roll it back
                raise TypeError(
                    "Attribute type must be Item/Enumeration class or "
                    "TypeReference",value
                )
            self.setDoc()   # update docstring

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
            if self.owner is not None and issubclass(self.owner,Item):
                inverse.type = self.owner

    inverse = property(
        lambda s: s._inverse, __setInverse, doc="""The inverse of this role"""
    )

    def __repr__(self):
        if self.name and self.owner:
            return "<Role %s of %s>" % (self.name,self.owner)
        return object.__repr__(self)

    def __getDoc(self):
        return self.__dict__.get('doc')

    def __setDoc(self,val):
        self.__dict__['doc'] = val
        self.setDoc()

    doc = description = property(__getDoc,__setDoc)

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
            (self.__class__.__name__, getattr(self.type,'__name__',None))
        )

    def _create_schema_item(self):
        if self.owner is None or self.name is None:
            raise TypeError(
                "role object used outside of schema.Item subclass"
            )

        attr = Attribute(self.name, None, itemFor(Attribute))
        self.__dict__['_schema_attr_'] = True   # disallow changes
        return attr

    def _init_schema_item(self, attr):
        kind = attr.itsParent = itemFor(self.owner)
        kind.attributes.append(attr, attr.itsName)
        # XXX self.registerAttribute(kind, attr)

        for aspect in all_aspects:
            if hasattr(self,aspect):
                val = getattr(self,aspect)
                if aspect=='displayName':
                    val = val or self.name  # default displayName=name
                elif aspect=='type':
                    if val is None:
                        continue    # don't set type to None
                    else:
                        val = itemFor(val)  # works for Kind and TypeReference

                setattr(attr,aspect,val)

        if not hasattr(self,'otherName') and self.inverse is not None:
            attr.otherName = self.inverse.name


class One(Role):
    cardinality = 'single'


class Many(Role):
    cardinality = 'set'


class Sequence(Role):
    cardinality = 'list'


class Mapping(Role):
    cardinality = 'dict'


class ItemClass(Activator):

    _kind_class = Kind

    def _create_schema_item(cls):
        return Kind(
            cls.__name__, parcel_for_module(cls.__module__), itemFor(Kind)
        )

    def _init_schema_item(cls,kind):
        kind.superKinds = [
            itemFor(b) for b in cls.__bases__ if issubclass(b,Item)
        ]
        kind.attributes = []
        kind.classes = {'python': cls }

        for attr in cls.__dict__.values():
            if isinstance(attr,Role):
                itemFor(attr)


class Item(Base):
    """Base class for schema-defined Kinds"""

    __metaclass__ = ItemClass

    def __init__(self,
        name=None, parent=None, kind=None, *args, **values
    ):
        if parent is None and name is None:
            parent = anonymous_root
        if kind is None:
            kind = itemFor(self.__class__)
        super(Item,self).__init__(name,parent,kind,*args,**values)


class EnumerationClass(Activator):
    """Metaclass for enumerations"""

    _kind_class = Types.Enumeration

    def __init__(cls,name,bases,cdict):
        for name,value in cdict.items():
            if name.startswith('__'):
                continue
            elif name!='values':
                raise TypeError(
                    "Only 'values' may be defined in an enumeration class",
                    name, value
                )
        super(EnumerationClass,cls).__init__(name,bases,cdict)
        try:
            Enumeration
        except NameError:
            return  # Enumeration itself doesn't need values

        if bases<>(Enumeration,):
            raise TypeError("Enumerations cannot subclass or be subclassed")

        values = cdict.get('values',())
        wrong = [v for v in values if not isinstance(v,str)]
        if not isinstance(values,tuple) or not values or wrong:
            raise TypeError(
                "'values' must be a tuple of 1 or more strings"
            )

    def _create_schema_item(cls):
        return Types.Enumeration(
            cls.__name__, parcel_for_module(cls.__module__),
            itemFor(Types.Enumeration)
        )

    def _init_schema_item(cls,enum):
        enum.values = list(cls.values)


class Enumeration(object):
    """Base class for defining enumerations"""
    __metaclass__ = EnumerationClass


def kindInfo(**attrs):
    """Declare metadata for a class' schema item

    The attributes defined by the keyword arguments will be set on the
    enclosing class' schema Item.  For example, the following class'
    repository Kind will have a ``displayName`` of ``"Example Item"``, and
    a ``displayAttribute`` of ``"someAttr"``::

        class SomeItem(schema.Item):
            schema.kindInfo(
                displayName = "Example Item",
                displayAttribute = "someAttr",
            )

    ``kindInfo()`` can only be used in the body of a class that derives from
    ``schema.Item`` or ``schema.Enumeration``, and it will only accept keywords
    that are valid attributes of the ``Kind`` or ``Enumeration`` kinds,
    respectively.

    (Note: if your class includes a ``__metaclass__`` definition, any calls to
    ``kindInfo`` must come *after* the ``__metaclass__`` assignment.)
    """

    from zope.interface.advice import getFrameInfo, addClassAdvisor
    kind, module, _locals, _globals = getFrameInfo(sys._getframe(1))

    if kind=='exec':
        # Fix for class-in-doctest-exec
        if '__module__' in _locals and _locals is not _globals:
            kind="class"

    if kind != "class":
        raise SyntaxError(
            "kindInfo() must be called in the body of a class statement"
        )

    info = _locals.setdefault('__kind_info__',{})
    for k,v in attrs.items():
        if k in info:
            raise ValueError("%r defined multiple times for this class" % (k,))
        info[k] = v

    def callback(cls):
        for k,v in attrs.items():
            if not hasattr(cls._kind_class, k):
                raise TypeError(
                    "%r is not an attribute of %s" %
                    (k, cls._kind_class.__name__)
                )
        return cls
    addClassAdvisor(callback)


def importString(name, globalDict=__main__.__dict__):
    """Import an item specified by a string

    Example Usage::

        attribute1 = importString('some.module:attribute1')
        attribute2 = importString('other.module:nested.attribute2')

    'importString' imports an object from a module, according to an
    import specification string: a dot-delimited path to an object
    in the Python package namespace.  For example, the string
    '"some.module.attribute"' is equivalent to the result of
    'from some.module import attribute'.

    For readability of import strings, it's sometimes helpful to use a ':' to
    separate a module name from items it contains.  It's optional, though,
    as 'importString' will convert the ':' to a '.' internally anyway.

    This routine was copied from PEAK's ``peak.util.imports`` module.
    """

    if ':' in name:
        name = name.replace(':','.')

    path  = []

    for part in filter(None,name.split('.')):
        if path:
            try:
                item = getattr(item, part)
                path.append(part)
                continue
            except AttributeError:
                pass

        path.append(part)
        item = __import__('.'.join(path), globalDict, globalDict, ['__name__'])

    return item



# --------------------
# Repository interface
# --------------------

def parcel_for_module(moduleName):
    """Return the Parcel for the named module

    If the named module has a ``__parcel__`` attribute, its value will be
    used to redirect to another parcel.  If the module does not have a
    ``__parcel__``, then a new parcel will be created, cached, and returned.
    If the module has a ``__parcel_class__`` attribute, it will be used in
    place of the ``application.Parcel.Parcel`` class, to create the parcel
    instance.  The ``__parcel_class__`` must accept three arguments: the
    parcel's name, its parent parcel (which will be the ``parcel_for_module()``
    of the module's enclosing package), and the Parcel Kind (as found at
    ``//Schema/Core/Parcel`` in the null repository view).

    If ``moduleName`` is an empty string, the ``//parcels`` root of the null
    repository view is returned.

    This routine is thread-safe and re-entrant.
    """
    global_lock.acquire()
    try:
        if moduleName:
            try:
                return nrv._parcel_cache[moduleName]
            except KeyError:
                module = importString(moduleName)

            if hasattr(module,'__parcel__'):
                nrv._parcel_cache[moduleName] = parcel = parcel_for_module(
                    module.__parcel__
                )
                return parcel

            if '.' in moduleName:
                parentName,modName = moduleName.rsplit('.',1)
            else:
                parentName,modName = '',moduleName

            mkParcel = getattr(module,'__parcel_class__',Parcel)

            nrv._parcel_cache[moduleName] = parcel = mkParcel(
                modName, parcel_for_module(parentName),
                nrv.findPath('//Schema/Core/Parcel')
            )

            declareTemplate(parcel)
            return parcel

        else:
            root = nrv.findPath('//parcels')
            if root is None:
                Manager.get(nrv,["x"])  # force setup of parcels root
                root = nrv.findPath('//parcels')
                declareTemplate(root)
            return root
    finally:
        global_lock.release()


def synchronize(repoView,moduleName):
    """Ensure that the named module's schema is incorporated into `repoView`"""
    module = importString(moduleName)
    for item in module.__dict__.values():
        if hasattr(item,'_create_schema_item'):
            # Import each kind
            repoView.importItem(itemFor(item))

    # Import the parcel, too, in case there were no kinds
    repoView.importItem(parcel_for_module(moduleName))


def itemFor(obj):
    """Return the schema Item corresponding to ``obj`` in the null view"""

    try:
        item = nrv._schema_cache[obj]
    except KeyError:
        pass
    else:
        if item is not None:
            return item

    global_lock.acquire()
    try:
        # Double-checked locking; somebody might've updated the cache while
        # we were waiting to acquire the lock
        if obj in nrv._schema_cache:
            item = nrv._schema_cache[obj]
            if item is None:
                # If we get here, it's because itemFor() has re-entered itself
                # looking for the same item, which can only happen if an
                # object's _create_schema_item() is cyclically recursive.
                # Don't do that.
                raise RuntimeError("Recursive schema item initialization")
            return item

        nrv._schema_cache[obj] = None   # guard against re-entry
        try:
            item = nrv._schema_cache[obj] = obj._create_schema_item()
        except:
            del nrv._schema_cache[obj]  # remove the guard
            raise
        else:
            declareTemplate(item)
            if isinstance(obj,type) and getattr(obj,'__doc__',None):
                item.description = obj.__doc__
            for k,v in getattr(obj,'__kind_info__',{}).items():
                setattr(item,k,v)
            obj._init_schema_item(item) # set up possibly-recursive data
            return item
    finally:
        global_lock.release()



# -------------------------------
# Initialization/Utility Routines
# -------------------------------

def initRepository(rv,
    packdir=os.path.join(os.path.dirname(repository.__file__),'packs')
):
    """Ensure repository view `rv` has been initialized with core schema"""

    # Initialize the core schema, if needed
    if rv.findPath('//Schema/Core/Item') is None:
        rv.loadPack(os.path.join(packdir,'schema.pack'))
    if rv.findPath('//Schema/Core/Parcel') is None:
        rv.loadPack(os.path.join(packdir,'chandler.pack'))

    anonymous_root = rv.findPath(ANONYMOUS_ROOT)
    if anonymous_root is None:
        anonymous_root = Base(
            ANONYMOUS_ROOT[2:], rv, rv.findPath('//Schema/Core/Item')
        )

def declareTemplate(item):
    """Declare that `item` is a template, and should be copied when it is
    imported into another repository view."""
    if isinstance(item,Base):
        item._status |= Base.COPYEXPORT
    return item

def reset(rv=None):
    """TESTING ONLY: Reset the schema API to use a different repository view

    This routine allows you to pass in a repository view that will then
    be used by the schema API; it also returns the previously-used view.
    It exists so that unit tests can roll back the API's state to a known
    condition before proceeding.
    """
    global nrv, anonymous_root

    global_lock.acquire()
    try:
        old_rv = nrv
        if rv is None:
            rv = NullRepositoryView()

        nrv = rv
        initRepository(nrv)
        if not hasattr(nrv,'_parcel_cache'):
            nrv._parcel_cache = {}
        if not hasattr(nrv,'_schema_cache'):
            nrv._schema_cache = {
                Kind: nrv.findPath('//Schema/Core/Kind'),
                Attribute: nrv.findPath('//Schema/Core/Attribute'),
                Parcel: nrv.findPath('//Schema/Core/Parcel'),
                Base: nrv.findPath('//Schema/Core/Item'),
                Item: nrv.findPath('//Schema/Core/Item'),
                Enumeration: nrv.findPath('//Schema/Core/Enumeration'),
                Types.Enumeration: nrv.findPath('//Schema/Core/Enumeration'),
            }
        anonymous_root = nrv.findPath(ANONYMOUS_ROOT)
        declareTemplate(anonymous_root)

        return old_rv
    finally:
        global_lock.release()



# ---------------------------
# Setup null view and globals
# ---------------------------

nrv = anonymous_root = None
reset(nrv)

core_types = """
Boolean String Integer Long Float Tuple List Set Class Dictionary
Date Time DateTime TimeDelta
Lob Symbol URL Complex UUID Path
""".split()

for name in core_types:
    globals()[name] = TypeReference("//Schema/Core/"+name)

__all__.extend(core_types)

