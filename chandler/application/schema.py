from repository.persistence.RepositoryView import nullRepositoryView as nrv
from repository.item.Item import Item as Base
from repository.schema.Kind import CDescriptor, Kind
from application.Parcel import Manager, Parcel

import __main__
defaultGlobalDict = __main__.__dict__

import os, repository, threading
packdir = os.path.join(os.path.dirname(repository.__file__),'packs')    # XXX
global_lock = threading.RLock()

__all__ = [
    'ActiveDescriptor', 'Activator', 'Role',
    'One', 'Many', 'Sequence', 'Mapping', 'Item', 'ItemClass',
    'importString', 'parcel_for_module',
]

# Initialize the core schema, if needed
if nrv.findPath('//Schema/Core/Item') is None:
    nrv.loadPack(os.path.join(packdir,'schema.pack'))
if nrv.findPath('//Schema/Core/Parcel') is None:
    nrv.loadPack(os.path.join(packdir,'chandler.pack'))


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
        if not hasattr(type(self),attr):
            raise TypeError("%r is not a public attribute of %r objects"
                % (attr,type(self).__name__))
        old = self.__dict__.get(attr)
        if old is not None and old<>value:
            raise TypeError(
                "Role objects are immutable; can't change %r once set" % attr
            )
        self._setattr(attr,value)
        if attr=='type':
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
            (self.__class__.__name__, getattr(self.type,'__name__',None))
        )


class One(Role):
    cardinality = 'single'


class Many(Role):
    cardinality = 'set'


class Sequence(Role):
    cardinality = 'list'


class Mapping(Role):
    cardinality = 'dict'


class ItemClass(Activator):
    @property
    def _schema_kind(cls):
        try:
            return cls.__dict__['_schema_kind_']
        except KeyError:
            pass

        global_lock.acquire()
        try:
            if '_schema_kind_' in cls.__dict__:
                # In case another thread set it up while we were waiting for
                # the lock (i.e., this is double-checked locking)
                return cls.__dict__['_schema_kind_']

            elif '_schema_kind' in cls.__dict__:
                # In case the class set its kind explicitly...
                kind = cls.__dict__['_schema_kind']

            else:
                # Create a new kind
                kind = Kind(
                    cls.__name__, parcel_for_module(cls.__module__),
                    nrv.findPath('//Schema/Core/Kind')
                )
                kind.superKinds = [
                    b._schema_kind for b in cls.__bases__ if issubclass(b,Item)
                ]

                # kind.classes['python'] = cls
                kind._values['classes'] = { 'python': cls }
                kind._values._setTransient('classes')
                kind._setupClass(cls)

            type.__setattr__(cls,'_schema_kind_',kind)
            return kind

        finally:
            global_lock.release()


class Item(Base):
    """Base class for schema-defined Kinds"""

    __metaclass__ = ItemClass

    _schema_kind = nrv.findPath('//Schema/Core/Item')   # bootstrap root class


def importString(name, globalDict=defaultGlobalDict):
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


def parcel_for_module(moduleName):
    """Return the Parcel for the named module

    If the named module has a ``__parcel__`` attribute, its value will be
    returned.  If the module does not have a ``__parcel__``, then a new parcel
    will be created and stored in the module's ``__parcel__`` attribute.  If
    the module has a ``__parcel_class__`` attribute, it will be used in place
    of the ``application.Parcel.Parcel`` class, to create the parcel instance.
    The ``__parcel_class__`` must accept three arguments: the parcel's name,
    its parent parcel (which will be the ``parcel_for_module()`` of the
    module's enclosing package), and the Parcel Kind (as found at
    ``//Schema/Core/Parcel`` in the null repository view).

    If ``moduleName`` is an empty string, the ``//parcels`` root of the null
    repository view is returned.

    This routine is thread-safe and re-entrant.
    """
    global_lock.acquire()
    try:
        if moduleName:
            module = importString(moduleName)
            try:
                return module.__parcel__
            except AttributeError:
                if '.' in moduleName:
                    parentName,modName = moduleName.rsplit('.',1)
                else:
                    parentName,modName = '',moduleName
                mkParcel = getattr(module,'__parcel_class__',Parcel)
                module.__parcel__ = parcel = mkParcel(
                    modName, parcel_for_module(parentName),
                    nrv.findPath('//Schema/Core/Parcel')
                )
                return parcel
        else:
            root = nrv.findPath('//parcels')
            if root is None:
                Manager.get(nrv,["x"])  # force setup of parcels root
                root = nrv.findPath('//parcels')
            return root
    finally:
        global_lock.release()
