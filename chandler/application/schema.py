from repository.persistence.RepositoryView import NullRepositoryView
from repository.item.Item import Item as Base
from repository.item.Query import KindQuery
from repository.schema.Kind import CDescriptor, Kind
from repository.schema.Attribute import Attribute
from repository.schema import Types
from repository.schema.Cloud import Cloud as _Cloud
from repository.schema.Cloud import Endpoint as _Endpoint
import __main__, repository, threading, os, sys

__all__ = [
    'ActiveDescriptor', 'Activator', 'Role', 'itemFor', 'kindInfo',
    'One', 'Many', 'Sequence', 'Mapping', 'Item', 'ItemClass',
    'importString', 'parcel_for_module', 'TypeReference', 'Enumeration',
    'Cloud', 'Endpoint', 'addClouds', 'Struct',
]

all_aspects = Attribute.valueAspects + Attribute.refAspects + \
    ('displayName','description','issues','examples')

global_lock = threading.RLock()


class ForwardReference:
    """Forward reference to a not-yet defined object"""

    def __init__(self,name,role):
        self.name = name
        self.role = role
        self.__name__ = name.split('.')[-1]

    def __repr__(self):
        return "ForwardReference(%r,%r)" % (self.name,self.role)

    def _find_schema_item(self,view):
        return itemFor(self.referent(),view)

    def __hash__(self):
        return id(self)

    def referent(self):
        if self.role.owner is None:
            if '.' in self.name:
                return importString(self.name)
        else:
            module = sys.modules[self.role.owner.__module__] 
            if '.' in self.name:
                return importString(self.name, module.__dict__)
            elif self.role.type is self:
                # Reference is to type, look in module
                return getattr(module,self.name)

        if self.role.inverse is self:
            # Reference is to role, look in type
            type = self.role.type
            if isinstance(type,ForwardReference):
                type = type.referent()
            return getattr(type, self.name)
        else:
            raise TypeError(
                "Can't resolve local forward reference %r from %r"
                % (self.name,self.role)
            )

    def __eq__(self,other):
        if self is other:
            return True
        elif isinstance(other,ForwardReference) and self.name==other.name:
            return True
        elif isinstance(other,ItemClass):
            fullname = other.__module__+'.'+other.__name__
            return self.name==fullname or fullname.endswith('.'+self.name)
        elif isinstance(other,Role) and other.owner is not None:
            fullname = '%s.%s.%s' % (
                other.owner.__module__, other.owner.__name__, other.name
            )
            return self.name==fullname or fullname.endswith('.'+self.name)
        try:
            me = self.referent()
        except ImportError:
            return False
        else:
            return other is me

    def __ne__(self,other):
        return not self.__eq__(other)

    
class TypeReference:
    """Reference a core schema type (e.g. Integer) by its repository path"""

    def __init__(self,path):
        if _get_nrv().findPath(path) is None:
            raise NameError("Type %r not found in the core schema" % (path,))
        self.path = path
        self.__name__ = path.split('/')[-1]

    def __repr__(self):
        return "TypeReference(%r)" % self.path

    def _find_schema_item(self,view):
        item = view.findPath(self.path)
        if item is None:
            raise TypeError("Unrecognized type", self.path)
        return item


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

    owner = type = _inverse = _frozen = None

    __slots__ = ['__dict__']
    __slots__.extend(all_aspects)

    def __new__(cls, type=None, **kw):
        return super(Role,cls).__new__(cls,kw.get('name'))

    def __init__(self,type=None,**kw):
        super(Role,self).__init__(kw.get('name'))
        if type is not None:
            if isinstance(type,str):
                type = ForwardReference(type, self)
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
            if isinstance(cls,ItemClass) and self.inverse is not None:
                if isinstance(self.inverse,ForwardReference):
                    return
                elif isinstance(self.inverse.inverse,ForwardReference):
                    self.inverse.inverse = self
                self.inverse.type = cls

    def _setattr(self,attr,value):
        """Private routine allowing bypass of normal setattr constraints"""
        super(Role,self).__setattr__(attr,value)

    def __setattr__(self,attr,value):       
        if not hasattr(type(self),attr):
            raise TypeError("%r is not a public attribute of %r objects"
                % (attr,type(self).__name__))
                
        old = getattr(self,attr,None)
        if old is not None and old<>value:
            raise TypeError(
                "Role objects are immutable; can't change %r of %r once set"
                % (attr,self)
            )
        elif old is None and self._frozen:
            raise TypeError(
                "Role object %r cannot be modified after use" % self
            )

        self._setattr(attr,value)

        if attr=='type' and value is not None:
            if not hasattr(value,"_find_schema_item"):
                self._setattr(attr,old) # roll it back
                raise TypeError(
                    "Attribute type must be Item/Enumeration class or "
                    "TypeReference",value
                )
            self.setDoc()   # update docstring

    def __setInverse(self,inverse):

        # Handle initial forward reference setting
        if isinstance(inverse,str):
            inverse = ForwardReference(inverse,self)
            if self._inverse is None:
                self._inverse = inverse     # initial setup, allow anything
                return

        if self._inverse is not inverse:    # No-op if no change
            self._inverse = inverse
            if not isinstance(inverse.inverse,ForwardReference):
                # Only backpatch if the other end isn't a forward ref
                try:
                    inverse.inverse = self
                except:
                    self._setattr('_inverse',None)  # roll back the change
                    raise

                if self.owner is not None and isinstance(self.owner,ItemClass):
                    inverse.type = self.owner

    inverse = property(
        lambda s: s._inverse, __setInverse, doc="""The inverse of this role"""
    )

    def __repr__(self):
        if self.name and self.owner:
            return "<Role %s of %s>" % (self.name,self.owner)
        return object.__repr__(self)

    def __setDoc(self,val):
        self.__dict__['doc'] = val
        self.setDoc()

    doc = property(lambda self: self.__dict__.get('doc',None),__setDoc)
    description = property(lambda self: self.__dict__.get('doc',''),__setDoc)

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

    def _find_schema_item(self, view):
        pass

    def _create_schema_item(self, view):
        if self.owner is None or self.name is None:
            raise TypeError(
                "role object used outside of schema.Item subclass"
            )

        if isinstance(self.inverse,ForwardReference):
            self.inverse = self.inverse.referent()  # force resolution now

        attr = Attribute(self.name, None, itemFor(Attribute, view))
        return attr

    def _init_schema_item(self, attr, view):
        kind = attr.itsParent = itemFor(self.owner, view)
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
                        val = itemFor(val, view)  # works for Kind and TypeReference

                setattr(attr,aspect,val)

        if not hasattr(self,'otherName') and self.inverse is not None:
            attr.otherName = self.inverse.name

        if not self._frozen:
            self._frozen = True   # disallow changes

class One(Role):
    cardinality = 'single'


class Many(Role):
    cardinality = 'set'


class Sequence(Role):
    cardinality = 'list'


class Mapping(Role):
    cardinality = 'dict'


class Endpoint(object):
    """Represent an endpoint"""

    def __init__(self, name, attribute, includePolicy="byValue",
        cloudAlias=None, method = None
    ):
        values = _get_nrv().findPath('//Schema/Core/IncludePolicy').values
        if includePolicy not in values:
            raise ValueError(
                "Unrecognized includePolicy: %r" % (includePolicy,)
            )
        if isinstance(attribute,str):
            attribute = attribute,  # make it a tuple
        elif not isinstance(attribute,(list,tuple)):
            raise TypeError(
                "Attribute must be a string, or a list/tuple of strings",
                attribute
            )
        self.name = name
        self.attribute = attribute
        self.includePolicy = includePolicy
        self.cloudAlias = cloudAlias
        self.method = method
        
    def make_endpoint(self, cloud, alias):
        ep = _Endpoint(
            self.name, cloud, itemFor(_Endpoint, cloud.itsView),
            attribute=list(self.attribute), includePolicy=self.includePolicy,
        )
        if self.cloudAlias is not None:
            ep.cloudAlias = self.cloudAlias
        if self.method is not None:
            ep.method = self.method
        declareTemplate(ep)
        return ep


class AttributeAsEndpoint(Endpoint):
    """Adapt a Role or attribute name to use as an Endpoint factory"""
    
    def __new__(cls, attr, policy):
        if isinstance(attr, Endpoint):
            if attr.includePolicy != policy:
                raise ValueError("Endpoint policy doesn't match group")
            return attr
        return super(AttributeAsEndpoint,cls).__new__(cls,None,(),policy)          
        
    def __init__(self, attr, policy):
        if isinstance(attr,str):
            super(AttributeAsEndpoint,self).__init__(attr,(attr,), policy)
        elif isinstance(attr,Role):
            self.attr = attr
            super(AttributeAsEndpoint,self).__init__(None,(),policy)
        else:
            raise TypeError("Not an endpoint: %r" % (attr,))

    def make_endpoint(self, cloud, alias):
        if self.name is None:
            name = self.attr.name
            if name is None:
                raise TypeError(
                    "role object used outside of schema.Item subclass",
                    self.attr
                )
            else:
                self.name = name
                self.attribute = name,
        return super(AttributeAsEndpoint,self).make_endpoint(cloud, alias)


class Cloud:
    """Represent a cloud as a set of endpoints grouped by policy

    The constructor takes zero or more "by value" endpoints, attributes, or
    attribute names, and keyword arguments to create policy groups.  For
    example::

        class anItem(OtherItem):
            foo = schema.One(schema.String)
            bar = schema.Sequence(Something)

            schema.addClouds(
                sharing = schema.Cloud(
                    foo, "displayName",
                    byCloud = [bar, OtherItem.someAttr],
                )
            )

    This creates a 'sharing' cloud that includes the ``foo`` and ``displayName``
    attributes by value, and the ``bar`` and ``someAttr`` attributes by cloud.
    Each keyword argument name must be a valid ``//Schema/Core/IncludePolicy``
    value, and the keyword argument value must be a list or tuple of Endpoint
    objects, attribute objects, or attribute names.
    """

    def __init__(self,*byValue,**groups):
        self.endpoints = [AttributeAsEndpoint(ep,'byValue') for ep in byValue]        
        for policy,group in groups.items():
            if not isinstance(group, (list,tuple)):
                raise TypeError("Endpoint groups must be lists or tuples")
            self.endpoints.extend(
                [AttributeAsEndpoint(ep,policy) for ep in group]
            )

    def make_cloud(self,kind,alias):
        cloud = _Cloud(alias.title()+"Cloud", kind, itemFor(_Cloud,kind.itsView))
        declareTemplate(cloud)
        cloud.endpoints = []
        for ep in self.endpoints:
            ep = ep.make_endpoint(cloud, alias)
            cloud.endpoints.append(ep, ep.itsName)
        return cloud

        
class ItemClass(Activator):
    """Metaclass for schema.Item"""

    _kind_class = Kind

    # Prevent __kind_info__ from being inherited by Item subclasses; each class
    # must define its own, if it has any.
    __kind_info__ = property(lambda cls: cls.__dict__.get('__kind_info__',{}))

    def __init__(cls, name, bases, cdict):
        if '__default_path__' in cdict:
            if isinstance(cls.__default_path__, basestring):
                cls.__default_path__ = ItemRoot.fromString(cls.__default_path__)
        super(ItemClass,cls).__init__(name,bases,cdict)

    def _find_schema_item(cls, view):
        parent = view.findPath(ModuleMaker(cls.__module__).getPath())
        if parent is not None:
            item = parent.getItemChild(cls.__name__)
            if isinstance(item,Kind) and item.getItemClass() is cls:
                return item
        
    def _create_schema_item(cls, view):
        return Kind(cls.__name__, None, itemFor(Kind, view))

    def _init_schema_item(cls, kind, view):
        kind.superKinds = [
            itemFor(b, view) for b in cls.__bases__
                if isinstance(b,ItemClass) or b in view._schema_cache
        ]

        kind.clouds = []
        for alias, cloud_def in cls.__dict__.get('__kind_clouds__',{}).items():
            kind.clouds.append(cloud_def.make_cloud(kind,alias), alias)

        kind.classes = {'python': cls }
        kind.attributes = []
        for name,attr in cls.__dict__.items():
            if isinstance(attr,Role):
                ai = itemFor(attr, view)
                if ai not in kind.attributes:
                    kind.attributes.append(ai,name)

        kind.itsParent = parcel_for_module(cls.__module__, view)


class ItemRoot:
    """Schema template for a named root"""

    def __init__(self,*parts):
        self.parts = parts

    @classmethod
    def fromString(cls, pathStr):
        path = pathStr.split('/')
        body = tuple(path[2:])
        if path[0] or path[1] or '' in body or '.' in body or '..' in body:
            raise ValueError(
                "Root paths must begin with // and be absolute", pathStr
            )
        return cls(*body)


    def _find_schema_item(self, view):
        item = view
        for part in self.parts:
            try:
                item = item[part]
            except KeyError:
                item = Item(part, item)
            declareTemplate(item)
        return item

    def __repr__(self):
        return "ItemRoot%r" % self.parts



class Item(Base):
    """Base class for schema-defined Kinds"""

    __metaclass__ = ItemClass
    __default_path__ = "//userdata"

    def __init__(self,
        name=None, parent=None, kind=None, view=None, *args, **values
    ):
        if kind is None or parent is None:
            if view is None:
                if parent is not None:
                    view = parent.itsView
                elif kind is not None:
                    view = kind.itsView
                else:
                    view = _get_nrv()
    
            if parent is None:
                parent = self.getDefaultParent(view)
    
            if kind is None:
                kind = self.getKind(view)

        super(Item,self).__init__(name,parent,kind,*args,**values)

    @classmethod
    def getDefaultParent(cls, view=None):
        if hasattr(cls,'__default_path__'):
            return itemFor(cls.__default_path__,view)
        return None

    @classmethod
    def getKind(cls, view=None):
        """Get the kind of this class (or instance) in the specified view"""
        return itemFor(cls,view)

    @classmethod
    def iterItems(cls, view=None, exact=False):
        """Yield instances of this type in the given view

        If `exact` is a true value, yield only exact matches, not subclass
        matches.  If `view` is omitted, the schema API's null repository view
        is used.
        """
        return KindQuery(not exact).run([itemFor(cls,view)])


class StructClass(Activator):
    """Metaclass for enumerations"""

    _kind_class = Types.Struct

    def __init__(cls,name,bases,cdict):
        super(StructClass,cls).__init__(name,bases,cdict)
        try:
            Struct
        except NameError:
            return  # Struct itself doesn't need fields

        if bases<>(Struct,):
            raise TypeError("Structs cannot subclass or be subclassed")

        values = cdict.get('__slots__',())
        wrong = [v for v in values if not isinstance(v,str)]
        if not isinstance(values,tuple) or not values or wrong:
            raise TypeError(
                "'__slots__' must be a tuple of 1 or more strings"
            )

    def _find_schema_item(cls, view):
        parent = parcel_for_module(cls.__module__, view)
        item = parent.getItemChild(cls.__name__)
        if isinstance(item,Types.Struct):
            return item
        
    def _create_schema_item(cls, view):
        return SchemaStruct(
            cls.__name__, parcel_for_module(cls.__module__, view),
            itemFor(Types.Struct, view)
        )

    def _init_schema_item(cls,typ, view):
        typ.fields = dict((k,{}) for k in cls.__slots__)
        typ.implementationTypes = {'python': cls}


class SchemaStruct(Types.Struct):

    def makeString(self, value):
        return repr(tuple(getattr(value,attr) for attr in value.__slots__))

    def makeValue(self,value):
        return self.getImplementationType()(*eval(value)) # XXX
        

class Struct(object):
    __metaclass__ = StructClass
    __slots__ = ()

    def __init__(self,*args,**kw):
        for k,v in kw.items():
            setattr(self,k,v)
        for k,v in zip(self.__slots__,args):
            setattr(self,k,v)
        if len(args)>len(self.__slots__):
            raise TypeError("Unexpected arguments", args[len(self.__slots__):])
        #for k in self.__slots__:
        #    if not hasattr(self,k):
        #        raise TypeError("No value supplied for %r field" % k)

    def __repr__(self):
        return "%s%r" % (
            self.__class__.__name__,
            tuple(getattr(self,attr) for attr in self.__slots__)
        )

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

    def _find_schema_item(cls, view):
        parent = parcel_for_module(cls.__module__, view)
        item = parent.getItemChild(cls.__name__)
        if isinstance(item,Types.Enumeration):
            return item

    def _create_schema_item(cls, view):
        return Types.Enumeration(
            cls.__name__, parcel_for_module(cls.__module__, view),
            itemFor(Types.Enumeration, view)
        )

    def _init_schema_item(cls, enum, view):
        enum.values = list(cls.values)


class Enumeration(object):
    """Base class for defining enumerations"""
    __metaclass__ = EnumerationClass


def _update_info(name,attr,data):
    from zope.interface.advice import getFrameInfo, addClassAdvisor
    kind, module, _locals, _globals = getFrameInfo(sys._getframe(2))

    if kind=='exec':
        # Fix for class-in-doctest-exec
        if '__module__' in _locals and _locals is not _globals:
            kind="class"

    if kind != "class":
        raise SyntaxError(
            name+"() must be called in the body of a class statement"
        )

    info = _locals.setdefault(attr,{})
    for k,v in data.items():
        if k in info:
            raise ValueError("%r defined multiple times for this class" % (k,))
        info[k] = v
    
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
    _update_info('kindInfo','__kind_info__',attrs)

    def callback(cls):
        for k,v in attrs.items():
            if not hasattr(cls._kind_class, k):
                raise TypeError(
                    "%r is not an attribute of %s" %
                    (k, cls._kind_class.__name__)
                )
        return cls

    from zope.interface.advice import addClassAdvisor
    addClassAdvisor(callback)


def addClouds(**clouds):
    """Declare clouds for a class' Kind

    Takes keyword arguments whose names define the clouds' aliases, and
    whose values are the ``schema.Cloud`` instances.  For example::
        
        class anItem(OtherItem):
            foo = schema.One(schema.String)
            bar = schema.Sequence(Something)

            schema.addClouds(
                sharing = schema.Cloud(foo, "displayName"),
                copying = schema.Cloud(byCloud = [bar]),
            )    
    """
    for cloud in clouds.values():
        if not isinstance(cloud,Cloud):
            raise TypeError("Not a schema.Cloud", cloud)
    _update_info('addClouds','__kind_clouds__',clouds)



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

class ModuleMaker:
    def __init__(self,moduleName):
        module = importString(moduleName)
        self.moduleName = getattr(module,'__parcel__',moduleName)
        if '.' in self.moduleName:
            self.parentName, self.name = self.moduleName.rsplit('.',1)
        else:
            self.parentName, self.name = None, self.moduleName

    def getPath(self):
        if self.moduleName.startswith('//'):
            return self.moduleName
        if self.parentName:
            return ModuleMaker(self.parentName).getPath()+'/'+self.name
        return '//parcels/'+self.name

    def getParent(self,view):
        if self.parentName:
            return parcel_for_module(self.parentName,view)
        else:
            root = view.findPath('parcels')
            if root is None:
                from application.Parcel import Parcel
                # Make sure the Parcel kind exists (which may cause //parcels
                # to get created through a recursive re-entry of this function)
                itemFor(Parcel, view)

                # Create //parcels *only* if it still doesn't exist yet
                root = view.findPath('parcels')
                if root is None:
                    root = Parcel('parcels',view)
                    declareTemplate(root)

            return root

    def __hash__(self):
        return hash(self.moduleName)

    def __eq__(self,other):
        return self.moduleName == other

    def _find_schema_item(self,view):
        if self.moduleName.startswith('//'):
            return view.findPath(self.moduleName)
        parent = self.getParent(view)
        item = parent.getItemChild(self.name)
        from application.Parcel import Parcel
        if isinstance(item,Parcel):
            return item

    def _get_parcel_factory(self, view):
        module = importString(self.moduleName)
        from application.Parcel import Parcel
        return getattr(module,'__parcel_class__',Parcel)
        
    def _create_schema_item(self,view):
        mkParcel = self._get_parcel_factory(view)
        if isinstance(mkParcel, ItemClass):
            # Avoid circular dependency if parcel kind might be inside parcel
            item = Base(self.name, view, None)
            item.__class__ = mkParcel
            return item
        from application.Parcel import Parcel
        kind = itemFor(Parcel, view)
        return mkParcel(self.name, self.getParent(view), kind)

    def _init_schema_item(self,item,view):
        mkParcel = self._get_parcel_factory(view)
        if isinstance(mkParcel, ItemClass):
            # Fixup parcel with right class/kind
            item.itsParent = self.getParent(view)
            item.itsKind = itemFor(mkParcel, view)
            if item.itsKind.itsParent is item:
                item.itsKind.itsParent = item.itsParent     # XXX FIXME!
            mkParcel.__init__(item)

    def __repr__(self):
        return "ModuleMaker(%r)" % self.moduleName

def parcel_for_module(moduleName, view=None):
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

    This routine is thread-safe and re-entrant.
    """
    if view is None:
        view = _get_nrv()
    try:
        return view._schema_cache[moduleName]   # fast path
    except (AttributeError, KeyError):
        return itemFor(ModuleMaker(moduleName), view)   # slow path


def synchronize(repoView,moduleName):
    """Ensure that the named module's schema is incorporated into `repoView`"""
    module = importString(moduleName)
    for item in module.__dict__.values():
        if hasattr(item,'_find_schema_item'):
            # Import each kind/struct/enum          
            itemFor(item,repoView)

    # Import the parcel, too, in case there were no kinds
    parcel_for_module(moduleName,repoView)


def itemFor(obj, view=None):
    """Return the schema Item corresponding to ``obj`` in the null view"""

    if view is None:
        view = _get_nrv()

    try:
        item = view._schema_cache[obj]
    except AttributeError:
        initRepository(view)
        item = view._schema_cache.get(obj)
        if item is not None:
            return item
    except KeyError:
        pass
    else:
        if item is not None:
            return item

    global_lock.acquire()
    try:
        # Double-checked locking; somebody might've updated the cache while
        # we were waiting to acquire the lock
        if obj in view._schema_cache:
            item = view._schema_cache[obj]
            if item is None:
                # If we get here, it's because itemFor() has re-entered itself
                # looking for the same item, which can only happen if an
                # object's _find_schema_item() or _create_schema_item() is
                # cyclically recursive.  Don't do that.
                raise RuntimeError("Recursive schema item initialization", obj)
            return item

        view._schema_cache[obj] = None   # guard against re-entry
        try:
            item = view._schema_cache[obj] = obj._find_schema_item(view)
        except:
            del view._schema_cache[obj]  # remove the guard
            raise
        else:
            if item is None:
                # couldn't find it, try creating it
                try:
                    item = view._schema_cache[obj] = obj._create_schema_item(view)
                except:
                    del view._schema_cache[obj]  # remove the guard
                    raise
                else:
                    declareTemplate(item)
                    if isinstance(obj,type) and getattr(obj,'__doc__',None):
                        item.description = obj.__doc__
                    for k,v in getattr(obj,'__kind_info__',{}).items():
                        setattr(item,k,v)
                    # set up possibly-recursive data
                    obj._init_schema_item(item,view) 
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
    if rv.findPath('//Packs/Chandler') is None:
        rv.loadPack(os.path.join(packdir,'chandler.pack'))

    if not hasattr(rv,'_schema_cache'):
        item_kind = rv.findPath('//Schema/Core/Item')
        rv._schema_cache = {
            Base: item_kind, Item: item_kind, 
        }

        # Make all core kinds available for subclassing, etc.
        for core_item in rv.findPath('//Schema/Core').iterChildren():
            if isinstance(core_item,Kind):
                cls = core_item.classes['python']
                core_item._setupClass(cls)
                if cls is not Base:
                    assert cls not in rv._schema_cache, (
                        "Two kinds w/same non-Item class in core schema",
                        cls,
                        core_item.itsPath,
                        rv._schema_cache[cls].itsPath
                    )
                    rv._schema_cache[cls] = core_item




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
    global nrv

    global_lock.acquire()
    try:
        old_rv = nrv
        if rv is None:
            rv = NullRepositoryView()

        nrv = rv
        initRepository(nrv)
        return old_rv

    finally:
        global_lock.release()



# ---------------------------
# Setup null view and globals
# ---------------------------

nrv = None

def _get_nrv():

    if nrv is None:
        reset()
    return nrv


core_types = """
Boolean String Symbol BString UString Integer Long Float 
Tuple List Set Class Dictionary Anything
Date Time DateTime TimeDelta 
Lob URL Complex UUID Path SingleRef
Text LocalizableString
""".split()

for name in core_types:
    globals()[name] = TypeReference("//Schema/Core/"+name)

__all__.extend(core_types)

