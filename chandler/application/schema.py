#   Copyright (c) 2003-2006 Open Source Applications Foundation
#
#   Licensed under the Apache License, Version 2.0 (the "License");
#   you may not use this file except in compliance with the License.
#   You may obtain a copy of the License at
#
#       http://www.apache.org/licenses/LICENSE-2.0
#
#   Unless required by applicable law or agreed to in writing, software
#   distributed under the License is distributed on an "AS IS" BASIS,
#   WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
#   See the License for the specific language governing permissions and
#   limitations under the License.


from chandlerdb.schema.c import Redirector
from repository.persistence.RepositoryView import NullRepositoryView
from repository.item.Item import Item as Base
from repository.item.Collection import CollectionClass as BaseCollectionClass
from repository.schema.Kind import CDescriptor, Kind
from repository.schema.Attribute import Attribute
from repository.schema import Types
from repository.schema.Cloud import Cloud as _Cloud
from repository.schema.Cloud import Endpoint as _Endpoint
from zope.interface.advice import getFrameInfo, addClassAdvisor
import __main__, repository, threading, os, sys

__all__ = [
    'ActiveDescriptor', 'Activator', 'Descriptor', 'itemFor', 'kindInfo',
    'One', 'Many', 'Sequence', 'Mapping', 'Item', 'ItemClass',
    'importString', 'parcel_for_module', 'TypeReference',
    'Enumeration', 'Cloud', 'Endpoint', 'addClouds', 'Struct',
    'assertResolved', 'Annotation', 'AnnotationItem',
    'observer',
]

all_aspects = Attribute.valueAspects + Attribute.refAspects + ('description',)

policy_values = (
    'byRef', 'byValue', 'byCloud', 'byRef', 'none', 'byMethod', 'literal'
)

default_schema = {
    Kind: ('description',),
    Base: ('description',)
}


# The next two functions are abominable hacks to work around the
# absence of generic functions.  Maybe this can be cleaned up in 0.7
# by adding RuleDispatch to the mix?  Or alternately, by defining
# Chandler's core schema using the schema API, rather than packs.
#
def _is_schema(ob):
    fsi = getattr(ob,'_find_schema_item',None)
    if fsi:
        return fsi.im_self is not None  # must be a *bound* method
    return ob is Base or ob is Kind

def _target_type(ob):
    if ob is Base or ob is Kind:
        return ob
    else:
        return ob.targetType()


class TypeReference:
    """Reference a core schema type (e.g. Integer) by its repository path"""

    def __init__(self,path):
        called_from_here = sys._getframe(1).f_globals is globals()
        self.path = path
        self.__name__ = path.split('/')[-1]

    def __repr__(self):
        return "TypeReference(%r)" % self.path

    def _find_schema_item(self,view):
        item = view.findPath(self.path)
        if item is None:
            raise TypeError("Unrecognized type", self.path)
        return item

    def targetType(self):
        return self

core_types = """
Boolean Symbol Importable Bytes Text Integer Long Float Decimal
Tuple List Set Class Dictionary Anything
Date Time DateTime DateTimeTZ TimeDelta TimeZone
Lob URL Complex UUID Path ItemRef NilValue
""".split()

for name in core_types:
    globals()[name] = TypeReference("//Schema/Core/"+name)

__all__.extend(core_types)

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

    def targetType(cls):
        """By default, backreferences to arbitrary classes go nowhere"""
        return None


class Descriptor(ActiveDescriptor,CDescriptor):
    """Descriptor for a schema-defined attribute"""

    owner = type = _inverse = _frozen = annotates = None

    __slots__ = ['__dict__']
    __slots__.extend(all_aspects)

    def __new__(cls, type=None, **kw):
        return super(Descriptor,cls).__new__(cls,kw.get('name'))

    def __init__(self,type=None,**kw):
        super(Descriptor,self).__init__(kw.get('name'))
        for docattr in 'description','doc':
            if docattr in kw:
                self.__setDoc(kw.pop(docattr))
        if type is not None:
            if isinstance(type,str):
                raise TypeError("Can't use a string for a type name")
            self.type = type
        for k,v in kw.items():
            if k!='name':   # XXX workaround CDescriptor not allowing name set
                setattr(self,k,v)
        self.setDoc()   # default the doc string

    def activateInClass(self,cls,name,set_type=True):
        """Descriptor was defined/used in class `cls` under name `name`"""
        if self.owner is None:
            self.owner = cls
            CDescriptor.__init__(self,name)
            if _target_type(cls) and self.inverse is not None:
                if set_type:
                    self.inverse.type = _target_type(cls)
                if self.inverse.name is None and self.type is not None:
                    self.inverse.annotates = (self.type,)
                    cls = self.owner
                    self.inverse.activateInClass(
                        cls, "%s.%s.%s.inverse" % (
                            parcel_name(cls.__module__), cls.__name__,
                            self.name.split('.')[-1]
                        ), False
                    )
            if '.' in name and hasattr(self,'initialValue'):
                raise TypeError(
                    "anonymous or annotation attribute %r cannot have"
                    " an initialValue" % self
                )

    def _setattr(self,attr,value):
        """Private routine allowing bypass of normal setattr constraints"""
        super(Descriptor,self).__setattr__(attr,value)

    def __setattr__(self,attr,value):
        if not hasattr(type(self),attr):
            raise TypeError("%r is not a public attribute of %r objects"
                % (attr,type(self).__name__))

        old = getattr(self,attr,None)
        if old is not None and old<>value:
            raise TypeError(
                "Descriptor objects are immutable; can't change %r of %r once set"
                % (attr,self)
            )
        elif old is None and self._frozen:
            raise TypeError(
                "Descriptor object %r cannot be modified after use" % self
            )

        self._setattr(attr, value)

        if attr=='type' and value is not None:
            if not _is_schema(value):
                self._setattr(attr,old) # roll it back
                raise TypeError(
                    "Attribute type must be Item/Enumeration class or "
                    "TypeReference",value
                )
            if _target_type(value):
                self._setattr(attr, _target_type(value))
            self.setDoc()   # update docstring

    def __setInverse(self,inverse):

        # Handle initial forward reference setting
        if isinstance(inverse,str):
            raise TypeError("Can't use a string for an inverse name")

        if self._inverse is not inverse:    # No-op if no change
            self._inverse = inverse
            try:
                inverse.inverse = self
            except:
                self._setattr('_inverse',None)  # roll back the change
                raise

            if self.owner and _target_type(self.owner):
                inverse.type = _target_type(self.owner)

    inverse = property(
        lambda s: s._inverse, __setInverse, doc="""The inverse of this role"""
    )

    def __repr__(self):
        if self.name and self.owner:
            return "<Descriptor %s of %s>" % (self.name,self.owner)
        return object.__repr__(self)

    def __setDoc(self,val):
        self.__dict__['doc'] = val
        self.setDoc()

    doc = property(lambda self: self.__dict__.get('doc',None),__setDoc)
    description = property(lambda self: self.__dict__.get('doc',''),__setDoc)

    def setDoc(self):
        doc = self.doc
        name = self.docInfo()
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
                "role object used outside of schema class"
            )

        attr = Attribute(None, view['Schema'], itemFor(Attribute, view))
        return attr

    def _init_schema_item(self, attr, view):
        kind = attr.itsParent = itemFor(self.owner, view)
        attr.itsName = self.name

        for aspect in all_aspects:
            if hasattr(self,aspect):
                val = getattr(self,aspect)
                if aspect=='type':
                    if val is None:
                        continue    # don't set type to None
                    else:
                        val = itemFor(val, view)  # works for Kind and TypeReference
                        if isinstance(val, AnnotationItem):
                            val = itemFor(val.annotates, view)
                setattr(attr,aspect,val)

        if not hasattr(self,'otherName') and self.inverse is not None:
            attr.otherName = self.inverse.name

        if not self._frozen:
            self._frozen = True   # disallow changes

        if self.annotates:
            for cls in self.annotates:
                kind = itemFor(cls, view)
                kind.attributes.append(attr, attr.itsName)

        if self.inverse is not None:
            itemFor(self.inverse, view)


class One(Descriptor):
    cardinality = 'single'


class Many(Descriptor):
    cardinality = 'set'


class Sequence(Descriptor):
    cardinality = 'list'


class Mapping(Descriptor):
    cardinality = 'dict'

class Calculated(property, ActiveDescriptor):
    __slots__ = ['basedOn', 'type', 'name']
    basedOn = ()
    type = name = None

    def __new__(cls, schema_type, basedOn, fget, fset=None, fdel=None,
                doc=None):
        return property.__new__(cls, fget, fset, fdel, doc)

    def __init__(self, schema_type, basedOn, fget, fset=None, fdel=None,
                 doc=None):
        property.__init__(self, fget, fset, fdel, doc)
        self.type = schema_type
        self.basedOn = basedOn

    def activateInClass(self,cls,name):
        if issubclass(cls, Annotation):
            def wrapForAnnotation(f):
                if f is None:
                    return None
                else:
                    def newFn(item, *args):
                        return f(cls(item), *args)
                    return newFn

            fullname = "%s.%s.%s" % (parcel_name(cls.__module__),
                                     cls.__name__, name)

            fset = wrapForAnnotation(self.fset)
            fget = wrapForAnnotation(self.fget)
            fdel = wrapForAnnotation(self.fdel)

            newProp = Calculated(self.type, self.basedOn, fget, fset=fset,
                                 fdel=fdel, doc=self.__doc__)
            self.name = fullname
            newProp.name = fullname

            setattr(_target_type(cls),fullname,newProp)
        else:
            self.name = name

        setattr(cls,name,self)


class Endpoint(object):
    """Represent an endpoint"""

    def __init__(self, name, attribute, includePolicy="byValue",
        cloudAlias=None, method = None
    ):
        if includePolicy not in policy_values:
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
        cloud.endpoints.append(ep, ep.itsName)
        return ep


class AttributeAsEndpoint(Endpoint):
    """Adapt a Descriptor or attribute name to use as an Endpoint factory"""

    def __new__(cls, attr, policy):
        if isinstance(attr, Endpoint):
            if attr.includePolicy != policy:
                raise ValueError("Endpoint policy doesn't match group")
            return attr
        return super(AttributeAsEndpoint,cls).__new__(cls,None,(),policy)

    def __init__(self, attr, policy):
        if isinstance(attr,str):
            super(AttributeAsEndpoint,self).__init__(attr,(attr,), policy)
        elif isinstance(attr,Descriptor) or hasattr(attr,'name'):
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
            foo = schema.One(schema.Text)
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
        cloud = kind.clouds.getByAlias(alias)
        if cloud is None:
            cloud = _Cloud(
                alias.title()+"Cloud", kind, itemFor(_Cloud,kind.itsView),
                endpoints = []
            )
            declareTemplate(cloud)
            kind.clouds.append(cloud, alias)

        for ep in self.endpoints:
            ep.make_endpoint(cloud, alias)
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
        return Kind(
            None, view['Schema'], itemFor(Kind, view), superKinds=[],
            clouds=[], attributes=[], classes={'python': cls}
        )

    def _init_schema_item(cls, kind, view):
        kind.superKinds = [
            itemFor(b, view) for b in cls.__bases__
                if isinstance(b,ItemClass) or b in view._schema_cache
        ]

        for alias, cloud_def in cls.__dict__.get('__kind_clouds__',{}).items():
            cloud_def.make_cloud(kind,alias)

        for name,attr in cls.__dict__.items():
            if isinstance(attr,Descriptor):
                ai = itemFor(attr, view)
                if ai not in kind.attributes:
                    kind.attributes.append(ai,name)

        for name, attrNames in cls.__dict__.get('__after_change__',{}).items():
            if name.startswith('__'):
                # support private name mangling
                name = '_%s%s' % (cls.__name__, name)
            for attrName in attrNames:
                if isinstance(attrName,Descriptor):
                    attr = itemFor(attrName, view)
                else:
                    attr = kind.getAttribute(attrName, True)
                if attr is not None:
                    if hasattr(attr, 'afterChange'):
                        afterChange = attr.afterChange
                        if name not in afterChange:
                            afterChange.append(name)
                    else:
                        attr.afterChange = [name]
                else:
                    view.logger.warn("no attribute '%s' defined for kind for %s",
                                 attrName, cls)

        def fixup():
            kind.itsParent = parcel_for_module(cls.__module__, view)
            kind.itsName = cls.__name__
            if hasattr(cls,'getDefaultParent'):
                cls.getDefaultParent(view)
        return fixup

    def update(cls, parcel, itsName, **attrs):
        """Ensure that there is a `name` child of `parent` with `attrs`

        If `parent` already has a child of name `name`, it is updated with
        `attrs` and its kind is set to match this class.  Otherwise, a new
        item of the class' kind is created with the given `attrs`.  Either
        way, the resulting item is returned.

        This classmethod is typically used in ``installParcel()`` functions to
        create and/or update parcel items.
        """
        item = parcel.getItemChild(itsName)
        if item is None:
            return cls(itsName, parcel, **attrs)
        else:
            resolveRef(parcel,itsName)
            item.itsKind = cls.getKind(parcel.itsView)
            for k,v in attrs.iteritems():
                setattr(item,k,v)
        return item

    def targetType(cls):
        """Backreferences to an Item class go to that class"""
        return cls


class CollectionClass(ItemClass, BaseCollectionClass):
    """The metaclass to use for declaring collection classes"""

    def __init__(cls, name, bases, clsdict):
        ItemClass.__init__(cls, name, bases, clsdict)
        BaseCollectionClass.__init__(cls, name, bases, clsdict)


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
                item = Base(part, item)
            declareTemplate(item)
        return item

    def __repr__(self):
        return "ItemRoot%r" % self.parts



class Item(Base):
    """Base class for schema-defined Kinds"""

    __metaclass__ = ItemClass
    __default_path__ = "//userdata"

    def __init__(self,
        itsName=None, itsParent=None, itsKind=None, itsView=None,*args,**values
    ):
        # Note: this uses __dict__.get() in order to avoid *inheriting*
        # the __abstract__ flag, which would make the subclasses abstract too!
        if self.__class__.__dict__.get('__abstract__'):
            raise TypeError(
                self.__class__.__name__+" is an abstract class; use a "
                "subclass instead"
            )
        if itsKind is None or itsParent is None:
            if itsView is None:
                if itsParent is not None:
                    itsView = itsParent.itsView
                elif itsKind is not None:
                    itsView = itsKind.itsView
                else:
                    raise AssertionError(
                        "View, kind, or parent must be specified"
                    )

            if itsParent is None:
                itsParent = self.getDefaultParent(itsView)

            if itsKind is None:
                itsKind = self.getKind(itsView)

        if values:
            for k in 'name','parent','kind','view':
                if k in values and not hasattr(self.__class__,k):
                    # Item's signature has changed; this code can go away
                    # later, but for now it's needed to catch old-style code
                    raise TypeError("No such parameter", k, values[k])

        super(Item,self).__init__(itsName,itsParent,itsKind,*args,**values)

    @classmethod
    def getDefaultParent(cls, view):
        if hasattr(cls,'__default_path__'):
            return itemFor(cls.__default_path__,view)
        return None

    @classmethod
    def getKind(cls, view):
        """Get the kind of this class (or instance) in the specified view"""
        return itemFor(cls,view)

    @classmethod
    def iterItems(cls, view, exact=False):
        """Yield instances of this type in the given view

        If `exact` is a true value, yield only exact matches, not subclass
        matches.  If `view` is omitted, the schema API's null repository view
        is used.
        """
        return itemFor(cls,view).iterItems(not exact)


class AnnotationItem(Item):
    """Persistent data for Annotation types"""
    annotates = One(Class)


class Comparator(ActiveDescriptor):
    # [@@@] grant -- need to make sure this only
    # works inside annotations

    def __init__(self, fn):
        self.fn = fn

    def activateInClass(self,cls,name):
        self.name = "%s.%s.%s" % (parcel_name(cls.__module__),
                                  cls.__name__, name)
        fn = self.fn
        targetType = _target_type(cls)
        def newFn(this, other):
            return fn(cls(this), cls(other))
        newFn.__name__ = name
        setattr(targetType, self.name, newFn)


class AnnotationClass(type):
    """Metaclass for annotation types"""

    _kind_class = AnnotationItem

    # Prevent __kind_info__ from being inherited by Annotation classes; each
    # class must define its own, if it has any.
    __kind_info__ = ItemClass.__kind_info__

    def __new__(cls,name,bases,cdict):
        cdict.setdefault('__slots__', [])
        return super(AnnotationClass,cls).__new__(cls,name,bases,cdict)

    def __init__(cls,name,bases,cdict):
        # We need to process Calculateds last, because the methods
        # they use may not have been added to the class yet.
        for name,ob in cdict.items():
            if isinstance(ob,Descriptor):
                basename = "%s.%s." % (parcel_name(cls.__module__), cls.__name__)
                ob.annotates = _target_type(cls),
                ob.activateInClass(cls,basename+name)
                setattr(cls,name,Redirector(ob))
            elif isinstance(ob,ActiveDescriptor):
                ob.activateInClass(cls,name)

    def _find_schema_item(cls, view):
        parent = view.findPath(ModuleMaker(cls.__module__).getPath())
        if parent is not None:
            item = parent.getItemChild(cls.__name__)
            if isinstance(item, AnnotationItem):
                return item

    def _create_schema_item(cls, view):
        return AnnotationItem(
            None, view['Schema']
        )

    def _init_schema_item(cls, annInfo, view):
        for attr in cls.__dict__.values():
            if isinstance(attr,Redirector):
                itemFor(attr.cdesc, view)     # ensure all attributes exist

        targetClass = cls.targetType()
        kind = itemFor(cls.targetType(), view)
        for alias, cloud_def in cls.__dict__.get('__kind_clouds__',{}).items():
            cloud_def.make_cloud(kind,alias)

        for name, attrNames in cls.__dict__.get('__after_change__',{}).items():
            if name.startswith('__'):
                name = '_%s%s' % (cls.__name__, name)
            name = "%s.%s.%s" % (parcel_name(cls.__module__),cls.__name__,name)
            # @@@ [grant] copy-n-paste job from ItemClass._init_schema_item
            for attrName in attrNames:
                if isinstance(attrName,Descriptor):
                    attr = itemFor(attrName, view)
                else:
                    attr = kind.getAttribute(attrName, True)
                if attr is not None:
                    if hasattr(attr, 'afterChange'):
                        afterChange = attr.afterChange
                        if name not in afterChange:
                            afterChange.append(name)
                    else:
                        attr.afterChange = [name]
                else:
                    view.logger.warn("no attribute '%s' defined for kind for %s",
                                 attrName, cls)
        def fixup():
            annInfo.itsParent = parcel_for_module(cls.__module__, view)
            annInfo.itsName = cls.__name__
        return fixup

    def targetType(cls):
        try:
            return cls.__kind_info__['annotates']
        except KeyError:
            raise TypeError(
                "Annotation must use schema.kindInfo(annotates=[classes])"
            )


class Annotation:
    """Base class for annotations"""
    __metaclass__ = AnnotationClass
    __kind_info__ = {'annotates':Item}
    __slots__ = ['itsItem']

    def __init__(self, itsItem):
        if isinstance(itsItem,Annotation):
            itsItem = itsItem.itsItem   # unwrap if annotation
        required = type(self).targetType()
        if not isinstance(itsItem, required):
            raise TypeError("%s requires a %s instance but got a %s instance" % (type(self),required,type(itsItem)))
        itemFor(type(self), itsItem.itsView)
        self.itsItem = itsItem

    def __repr__(self):
        return "%s(%r)" % (type(self).__name__, self.itsItem)

    def __eq__(self, other):
        # Note: we use "==" here to compare items because either might be a
        # recurrence proxy, and "is" can't be used to compare proxied items.
        return type(other) == type(self) and self.itsItem == other.itsItem

    def __ne__(self, other):
        return not self.__eq__(other)

    @classmethod
    def addIndex(cls, collection, name, type, **keywds):
        # compare is tricky, since it takes a method name,
        # but that might not be defined on the item class.
        compare = keywds.get('compare', None)
        if compare is not None:
            compare = getattr(cls, compare)
            if not isinstance(compare, Comparator):
                raise ValueError, "'compare' value must be a schema.Comparator"

            keywds['compare'] = compare.name

        for key in ('attributes', 'monitor'):
            unconverted = keywds.get(key, None)
            if unconverted is not None:
                try:
                    keywds[key] = tuple(x.name for x in unconverted)
                except TypeError:
                    keywds[key] = unconverted.name

        attribute = keywds.get('attribute')
        if attribute is not None:
            keywds['attribute'] = attribute.name

        return collection.addIndex(name, type, **keywds)



class StructClass(Activator):
    """Metaclass for struct types"""

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
        parent = view.findPath(ModuleMaker(cls.__module__).getPath())
        if parent is not None:
            item = parent.getItemChild(cls.__name__)
            if isinstance(item,Types.Struct):
                return item

    def _create_schema_item(cls, view):
        return SchemaStruct(
            None, view['Schema'],
            itemFor(Types.Struct, view)
        )

    def _init_schema_item(cls,typ, view):
        typ.fields = dict((k,{}) for k in cls.__slots__)
        typ.implementationTypes = {'python': cls}
        def fixup():
            typ.itsParent = parcel_for_module(cls.__module__, view)
            typ.itsName = cls.__name__
        return fixup


class SchemaStruct(Types.Struct):

    def makeString(self, value):
        return repr(tuple(getattr(value,attr) for attr in value.__slots__))

    def makeValue(self,value):
        return self.getImplementationType()(*eval(value)) # XXX

    def writeValue(self, itemWriter, buffer, item, version, value, withSchema):
        writeValue = getattr(self.getImplementationType(), 'writeValue', None)
        if writeValue is not None:
            return writeValue(value, itemWriter, buffer)
        else:
            return super(SchemaStruct, self).writeValue(itemWriter, buffer,
                                                        item, version, value,
                                                        withSchema)

    def readValue(self, itemReader, offset, data, withSchema, view, name,
                  afterLoadHooks):
        readValue = getattr(self.getImplementationType(), 'readValue', None)
        if readValue is not None:
            return readValue(itemReader, offset, data)
        else:
            return super(SchemaStruct, self).readValue(itemReader, offset, data,
                                                       withSchema, view, name,
                                                       afterLoadHooks)

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


class SchemaEnumValue(Types.EnumValue):

    def __init__(self, enumClass, name, value):
        super(SchemaEnumValue, self).__init__(enumClass.__name__, name, value)
        self.enumClass = enumClass

    def getTypeItem(self, view):
        return itemFor(self.enumClass, view)


class EnumerationClass(Activator):
    """Metaclass for enumerations"""

    _kind_class = Types.Enumeration

    def __init__(cls,name,bases,cdict):
        for name,value in cdict.items():
            if name.startswith('__'):
                continue
            elif (name not in ('values', 'names') or
                  name == 'values' and 'names' in cdict or
                  name == 'names' and 'values' in cdict):
                raise TypeError(
                    "Only 'values' or 'names' may be defined in an enumeration class",
                    name, value
                )
        super(EnumerationClass,cls).__init__(name,bases,cdict)
        try:
            Enumeration
        except NameError:
            return  # Enumeration itself doesn't need values

        if bases<>(Enumeration,):
            raise TypeError("Enumerations cannot subclass or be subclassed")

        names = cdict.get('names', ())
        if names:
            values = dict(zip(names, range(len(names))))
        else:
            values = cdict.get('values', ())
        if isinstance(values, tuple):
            wrong = [v for v in values if not isinstance(v, str)]
        elif isinstance(values, dict):
            wrong = [n for n, v in values.iteritems() if not isinstance(n, str)]
            if not wrong:
                cls.constants = [SchemaEnumValue(cls, n, v)
                                 for n, v in values.iteritems()]
                for constant in cls.constants:
                    setattr(cls, constant.name, constant)
        else:
            wrong = values
        if not values or wrong:
            raise TypeError(
                "'values' must be a tuple of 1 or more strings or a dict of (str, value) pairs"
            )

    def _find_schema_item(cls, view):
        parent = view.findPath(ModuleMaker(cls.__module__).getPath())
        if parent is not None:
            item = parent.getItemChild(cls.__name__)
            if isinstance(item,Types.Enumeration):
                return item

    def _create_schema_item(cls, view):
        if hasattr(cls, 'constants'):
            names = getattr(cls, 'names', None)
            if names is not None:
                values = zip(names, range(len(names)))
            else:
                values = cls.values.items()
            return Types.ConstantEnumeration(
                None, view['Schema'], itemFor(Types.ConstantEnumeration, view),
                values=values
            )
        else:
            return Types.Enumeration(
                None, view['Schema'], itemFor(Types.Enumeration, view),
                values=list(cls.values)
            )

    def _init_schema_item(cls, enum, view):
        def fixup():
            enum.itsParent = parcel_for_module(cls.__module__, view)
            enum.itsName = cls.__name__
        return fixup



class Enumeration(object):
    """Base class for defining enumerations"""
    __metaclass__ = EnumerationClass
    values = ()

def _update_info(name,attr,data,frame=None,depth=2):
    frame = frame or sys._getframe(depth)
    kind, module, _locals, _globals = getFrameInfo(frame)

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
    repository Kind will have a ``displayAttribute`` of ``"someAttr"``::

        class SomeItem(schema.Item):
            schema.kindInfo(
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

    @addClassAdvisor
    def callback(cls):
        for k,v in attrs.items():
            kc = cls._kind_class
            kcs = getattr(kc, '__core_schema__', ())
            kcs = kcs or default_schema.get(kc) or ()
            if not hasattr(kc, k) and k not in kcs:
                raise TypeError(
                    "%r is not an attribute of %s" %
                    (k, cls._kind_class.__name__)
                )
        return cls


def addClouds(**clouds):
    """Declare clouds for a class' Kind

    Takes keyword arguments whose names define the clouds' aliases, and
    whose values are the ``schema.Cloud`` instances.  For example::

        class anItem(OtherItem):
            foo = schema.One(schema.Text)
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


def observer(*attrs):
    """Decorator to create an observer method for `attrs`"""
    attrs = list(attrs)
    for attr in attrs:
        if not isinstance(attr, Descriptor):
            raise TypeError(
                repr(attr)+
                " is not a schema.Descriptor (One, Many, Sequence, etc.)"
            )
    def decorator(func):
        _update_info('observer', '__after_change__', {func.__name__:attrs})
        @addClassAdvisor
        def callback(cls):
            for attr in attrs:
                if attr.owner is None or not issubclass(_target_type(cls), _target_type(attr.owner)):
                    raise TypeError(
                        "%r does not belong to %r or its superclasses"
                        % (attr, cls)
                    )
            if issubclass(cls, Annotation):
                targetClass = cls.targetType()
                afterChanges = cls.__dict__.get('__after_change__', {})
                for name, attrNames in afterChanges.items():

                    if name.startswith('__'):
                        # support private name mangling
                        name = '_%s%s' % (cls.__name__, name)

                    def makeNewMethod(cls, fullname, name):
                        meth = getattr(cls,name)
                        def wrappedMethod(item, op, attrName):
                            return meth(cls(item), op, attrName)
                        wrappedMethod.__name__ = name
                        wrappedMethod.__doc__ = meth.__doc__
                        return wrappedMethod

                    shortName = name
                    name = "%s.%s.%s" % (parcel_name(cls.__module__),
                                         cls.__name__, name)
                    setattr(targetClass, name,
                            makeNewMethod(cls, name, shortName))
            return cls
        return func

    return decorator


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


def getCaller(frame=None, level=2):
    frame = frame or sys._getframe(level)
    return frame.f_code.co_filename, frame.f_lineno

# --------------------
# Repository interface
# --------------------

class ns(object):
    """Shortcut namespace for referring to classes and instances in a parcel

    Example::

        current = schema.ns("osaf.current", repo_view)
        me = current.Contact.item

    The ``ns`` object acts almost like an XML namespace in parcel.xml, only in
    Python.  The main difference is that names defined in the module given will
    take precedence over items in the corresponding parcel.  See schema_api.txt
    for a more detailed explanation
    """

    def __init__(self, name, view):
        self.view = getattr(view,'itsView',view)
        self.__module = importString(name)

    def fwdRef(self, cls, name):
        return fwdRef(self.parcel, name, cls, getCaller())

    def __getattr__(self, name):
        if name.startswith('_'):
            raise AttributeError("No delegation for private attributes")
        if name=='parcel':
            self.parcel = parcel_for_module(self.__module.__name__, self.view)
            return self.parcel

        try:
            return getattr(self.__module,name)
        except AttributeError:
            value = self.parcel.getItemChild(name)
            if value is not None:
                return value
        raise AttributeError(
            "%s is not in %r or %r" % (name, self.__module, self.parcel)
        )

    def _makeTemplates(self):
        result = {}
        for k,v in self.__module.__dict__.items():
            if isinstance(v, ItemClass):
                result[k] = v.template
        return result

def _refMap(ob):
    view = ob.itsView
    try:
        return view._schema_fwdrefs
    except AttributeError:
        initRepository(view)
        return view._schema_fwdrefs


def fwdRef(parent, name, cls=Item, callerInfo=None):
    """Get child `name` of `parent`, creating a new kindless item if needed

    If the item didn't exist or is a forward reference, the caller is logged
    as the source of the forward reference so that ``assertResolved()`` can
    identify the source of the broken reference if it remains unresolved.
    Forward references can be marked resolved using ``resolveRef()``.
    """
    refs = _refMap(parent)
    item = parent.getItemChild(name)
    if item is None:
        # New forward reference
        item = cls(name, parent)
        refs[parent,name] = [callerInfo or getCaller()]
    else:
        callers = refs.get((parent,name))
        if callers is not None:
            # item was found, but it's a fwdref
            callers.append(callerInfo or getCaller())
    return item


def resolveRef(parent, name):
    """Mark the forward reference to (parent,name) resolved

    Normally, this is called by the ItemClass.update() method."""
    try:
        del _refMap(parent)[parent,name]
    except KeyError:
        pass

def assertResolved(view):
    """Assert that all forward references in `view` have been resolved

    If any forward references have not been resolved, raise an error listing
    them."""
    if not _refMap(view):
        return  # nothing to see, move along

    from cStringIO import StringIO
    s = StringIO()

    print >>s,"Unresolved forward references:"
    for (p,n), callers in _refMap(view).items():
        print >>s
        print >>s,"    %s/%s:" % (p.itsPath, n)
        for f,l in callers:
            print >>s,"        %s line %d" % (f,l)

    raise NameError(s.getvalue())


def parcel_name(moduleName):
    """Get a module's __parcel__ or __name__"""
    module = importString(moduleName)
    return getattr(module,'__parcel__',moduleName)


class ModuleMaker:
    def __init__(self,moduleName):
        self.moduleName = parcel_name(moduleName)
        if '.' in self.moduleName:
            self.parentName, self.name = self.moduleName.rsplit('.',1)
        else:
            self.parentName, self.name = None, self.moduleName

    def getPath(self):
        if self.moduleName.startswith('//'):
            # kludge to support putting Parcel + Manager in //Schema/Core
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
            # kludge to support putting Parcel + Manager in //Schema/Core
            return view.findPath(self.moduleName)
        if self.parentName:
            # Don't try to create the parent; if it doesn't exist just
            # fail the find operation.
            parent = ModuleMaker(self.parentName)._find_schema_item(view)
            if parent is None:
                return None
        else:
            # The root is okay to create during a find, since it can't
            # create a cycle
            parent = self.getParent(view)
        item = parent.getItemChild(self.name)
        from application.Parcel import Parcel
        if isinstance(item,Parcel):
            return item

    def _create_schema_item(self,view):
        # Create a temporary item without a kind, so as not to
        # incur unintended circularities.
        return Base(None, view['Schema'], None)

    def _init_schema_item(self,item,view):
        from application.Parcel import Parcel
        item.itsParent = self.getParent(view)
        item.itsName = self.name
        item.itsKind = itemFor(Parcel, view)

        # make sure that the schema for the module is fully created
        module = importString(self.moduleName)
        if hasattr(module,'installParcel'):
            synchronize(view, self.moduleName)
            module.installParcel(item, None)
        else:
            return lambda: synchronize(view, self.moduleName)


    def __repr__(self):
        return "ModuleMaker(%r)" % self.moduleName


def parcel_for_module(moduleName, view):
    """Return the Parcel for the named module

    If the named module has a ``__parcel__`` attribute, its value will be
    used to redirect to another parcel.  If the module does not have a
    ``__parcel__``, then a new parcel will be created, cached, and returned.

    This routine is thread-safe and re-entrant.
    """
    try:
        ob = view._schema_cache[moduleName]   # fast path
        if ob is None:
            # If we're here, it's because we tried to create a parcel while
            # looking for it.  Bad dog, no biscuit.
            raise RuntimeError(
                "Recursive schema item initialization: "+moduleName
            )
        return ob
    except (AttributeError, KeyError):
        return itemFor(ModuleMaker(moduleName), view)   # slow path


def synchronize(repoView,moduleName):
    """Ensure that the named module's schema is incorporated into `repoView`"""
    module = importString(moduleName)

    # Create the parcel first
    parcel_for_module(moduleName,repoView)

    for item in module.__dict__.values():
        if _is_schema(item):
            # Import each kind/struct/enum
            itemFor(item,repoView)



def itemFor(obj, view):
    """Return the schema Item corresponding to ``obj`` in the given view"""

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
                level = view._schema_init_level
                queue = view._schema_init_queue
                try:
                    view._schema_init_level += 1  # prevent recursion
                    cb = obj._init_schema_item(item,view)
                    if cb is not None:
                        queue.append(cb)
                    while queue and not level:
                        queue.pop(0)()  # invoke callbacks
                finally:
                    view._schema_init_level = level

        return item

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
        rv._schema_fwdrefs = {}
        rv._schema_cache = {
            Base: item_kind, Item: item_kind,
        }
        rv._schema_init_level = 0
        rv._schema_init_queue = []

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
    # The below is temporarily disabled because repository.tests.TestImport
    # relies on core schema not being COPYEXPORT; however, if we want to
    # support dynamic schema transfer AND viewless item creation, we'll need
    # to put it back and fix TestImport (and maybe the rest of the core schema)
    #
    #if isinstance(item,Base):
    #    item._status |= Base.COPYEXPORT
    return item

