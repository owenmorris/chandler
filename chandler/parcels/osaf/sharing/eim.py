__all__ = [
    'UnknownType', 'typeinfo_for', 'BytesType', 'TextType', 'DateType',
    'IntType', 'LobType', 'get_converter', 'add_converter', 'subtype',
    'typedef',
]

from simplegeneric import generic
from weakref import WeakValueDictionary
import linecache, os

@generic
def get_converter(context):
    """Return a conversion function for encoding in the `context` type context
    """
    ctx = typeinfo_for(context)

    if isinstance(context,type) and issubclass(context, TypeInfo):
        # prevent infinite recursion for unregistered primitive types
        # if this error occurs, somebody added a new primitive type without
        # creating a base conversion function for it
        raise AssertionError("Unregistered metatype", ctx)

    return get_converter(ctx)

@generic
def default_converter(value):
    raise TypeError(
        "No converter registered for values of type %r" % type(value)
    )

def add_converter(context, from_type, converter):
    """Register `converter` for converting `from_type` in `context`"""
    # XXX if converters cached by record types, add hooks here for updating
    gf = get_converter(context)
    if not get_converter.has_object(context):
        gf = generic(gf)    # extend base function
        get_converter.when_object(context)(lambda context: gf)
    gf.when_type(from_type)(converter)



class UnknownType(KeyError):
    """An object was not recognized as a type, alias, context, or URI"""


@generic
def typeinfo_for(context):
    """Return the relevant ``sharing.TypeInfo`` for `context`

    `context` may be a URI string, a ``sharing.TypeInfo``, ``sharing.Field``,
    or ``schema.Descriptor`` (e.g. ``schema.One``, etc.).  object.  It can also
    be any object registered as a type alias using ``sharing.typedef()``.

    The return value is a ``sharing.TypeInfo``.  If no type information is
    available for `context`, raise ``sharing.UnknownType``
    """
    raise UnknownType(context)


types_by_uri = WeakValueDictionary()

@typeinfo_for.when_type(str)
def lookup_by_uri(context):
    try:
        return types_by_uri[context]
    except KeyError:
        return typeinfo_for.default(context)


def typedef(alias, typeinfo):
    """Register `alias` as an alias for `typeinfo`

    `alias` may be any object.  `typeinfo` must be a type context, i.e.,
    ``typeinfo_for()`` should return a ``TypeInfo`` for it.  (Which means it
    can be a ``TypeInfo``, a URI, or a registered alias, field, etc.)
    An error occurs if `alias` is already registered."""
    typeinfo = typeinfo_for(typeinfo)   # unaliases and validates typeinfo
    typeinfo_for.when_object(alias)(lambda context: typeinfo)




class TypeInfo(object):
    size = None
    abstract = True
    __slots__ = 'uri', '__weakref__'

    def __init__(self, uri=None):
        if self.__class__.__dict__.get('abstract'):
            raise TypeError(
                "sharing.%s is an abstract type; use a subtype"
                % self.__class__.__name__
            )
        if uri is not None and uri in types_by_uri:
            raise TypeError("A type already exists for "+repr(uri))
        self.uri = uri
        types_by_uri[uri] = self

    def __setattr__(self, attr, value):
        if hasattr(self, 'uri'):    # have we been initialized?
            raise TypeError(
                "sharing.%s instances are immutable" % self.__class__.__name__
            )
        object.__setattr__(self, attr, value)

    def __repr__(self):
        return 'sharing.%s(%r)' % (
            self.__class__.__name__, self.uri
        )

    def clone(self, uri=None, *args, **kw):
        return self.__class__(uri, *args, **kw)

@get_converter.when_type(TypeInfo)
def get_default_converter_for_primitive_type(context):
    return get_converter(type(context))

@typeinfo_for.when_type(TypeInfo)
def return_typeinfo(context):
    return context  # TypeInfo can be used as-is



class SizedType(TypeInfo):
    abstract = True
    __slots__ = 'size'

    def __init__(self, uri=None, size=None):
        if size is None:
            raise TypeError(
                "size must be specified when creating a sharing."
                + self.__class__.__name__
            )
        self.size = size
        TypeInfo.__init__(self, uri)

    def __repr__(self):
        return 'sharing.%s(%r, %d)' % (
            self.__class__.__name__, self.uri, self.size
        )

    def clone(self, uri=None, size=None, *args, **kw):
        if size is None:
            size = self.size
        return self.__class__(uri, size, *args, **kw)

class BytesType(SizedType): __slots__ = ()
class TextType(SizedType):  __slots__ = ()
class IntType(TypeInfo):    __slots__ = ()
class DateType(TypeInfo):   __slots__ = ()
class LobType(TypeInfo):    __slots__ = ()

# define aliases so () is optional for anonymous unsized field types
typedef(IntType,  IntType())
typedef(LobType,  LobType())
typedef(DateType, DateType())








# Monkeypatch linecache to not throw out lines that don't come from files
# This patch is only needed for Python 2.4, as identical code is part of
# the linecache module in Python 2.5.  As soon as we go to 2.5, we can remove
# all of this code down to the '### END' marker below.
#
def checkcache(filename=None):
    """Discard cache entries that are out of date.
    (This is not checked upon each call!)"""

    if filename is None:
        filenames = linecache.cache.keys()
    else:
        if filename in linecache.cache:
            filenames = [filename]
        else:
            return

    for filename in filenames:
        size, mtime, lines, fullname = linecache.cache[filename]
        if mtime is None:
            continue   # no-op for files loaded via a __loader__
        try:
            stat = os.stat(fullname)
        except os.error:
            del linecache.cache[filename]
            continue
        if size != stat.st_size or mtime != stat.st_mtime:
            del linecache.cache[filename]

linecache.checkcache = checkcache

### END









def _constructor_for(name, cdict, fields):
    fname = "EIM-Generated Constructor for %s.%s" % (cdict['__module__'],name)
    args =', '.join(f.name for f in fields)
    conversions = ''.join(
        "\n    %s = get_converter(cls.%s)(%s)" % (f.name,f.name,f.name)
        for f in fields
    )
    source = (
        "def __new__(cls, %(args)s):%(conversions)s\n"
        "    return tuple.__new__(cls, (cls, %(args)s))""" % locals()
    )
    # Push the source into the linecache
    lines = [line+'\n' for line in source.splitlines()]
    linecache.cache[fname] = 0, None, lines, fname
    return compile(source, fname, "exec")


























class RecordClass(type):
    def __new__(meta, name, bases, cdict):
        try:
            Record
        except NameError:
            pass
        else:
            if bases != (Record,):
                raise TypeError("Record classes cannot be subclassed")
        fields = []
        for attr, val in cdict.items():
            if isinstance(val, field):
                if val.owner is not None:
                    raise TypeError(
                        "Can't reuse field '%s.%s' as '%s.%s'" %
                        (val.owner.__name__, val.name, name, attr)
                    )
                val.name = attr
                fields.append(val)

        fields.sort()
        cdict['__slots__'] = ()
        cdict['__fields__'] = tuple(fields)
        exec _constructor_for(name, cdict, fields) in globals(), cdict
        cls = type.__new__(meta, name, bases, cdict)
        for n,f in enumerate(fields):
            f.owner = cls
            f.offset = n+1
        return cls












_field_num = 1

class field(object):
    __slots__ = "owner", "name", "type", "typeinfo", "seq", "offset"
    def __init__(self, type):
        global _field_num
        self.owner = self.name = None
        self.type = type
        self.typeinfo = typeinfo_for(type)
        self.seq = _field_num = _field_num + 1

    def __setattr__(self, attr, val):
        if hasattr(self,'offset'):
            raise TypeError("field objects are immutable")
        super(field, self).__setattr__(attr, val)

    def __cmp__(self, other):
        if isinstance(other, field):
            return cmp(self.seq, other.seq)
        return cmp(id(self), id(other))

    def __get__(self, ob, typ=None):
        if ob is None:
            return self
        return ob[self.offset]

@typeinfo_for.when_type(field)
def return_typeinfo(context):
    return context.typeinfo

class Record(tuple):
    __slots__ = ()
    __metaclass__ = RecordClass
    def __repr__(self):
        r = "%s%r" % (self.__class__.__name__, self[1:])
        if r.endswith(',)'):
            return r[:-2]+')'
        return r



def create_default_converter(t):
    converter = generic(default_converter)
    get_converter.when_object(t)(lambda ctx: converter)

map(create_default_converter,
    [BytesType, TextType, IntType, DateType, LobType]
)

add_converter(IntType, int, int)


def subtype(typeinfo, *args, **kw):
    """XXX"""
    newti = typeinfo_for(typeinfo).clone(*args, **kw)
    gf = generic(get_converter(typeinfo))
    get_converter.when_object(newti)(lambda ctx:gf)
    return newti

def test_suite():
    import doctest
    return doctest.DocFileSuite(
        'EIM.txt',
        optionflags=doctest.ELLIPSIS|doctest.REPORT_ONLY_FIRST_FAILURE,
    )

















