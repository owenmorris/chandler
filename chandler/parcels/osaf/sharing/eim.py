#   Copyright (c) 2006-2007 Open Source Applications Foundation
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

__all__ = [
    'UnknownType', 'typeinfo_for', 'BytesType', 'TextType', 'DateType',
    'IntType', 'BlobType', 'ClobType', 'DecimalType', 'get_converter',
    'add_converter', 'subtype', 'typedef', 'field', 'key', 'NoChange',
    'Record', 'RecordSet', 'lookupSchemaURI', 'Filter', 'Translator',
    'exporter', 'TimestampType', 'IncompatibleTypes', 'Missing'
]
from symbols import Symbol  # XXX change this to peak.util.symbols
from simplegeneric import generic
from weakref import WeakValueDictionary
import linecache, os, decimal, datetime
from application import schema
from chandlerdb.util.c import UUID
from osaf import pim
import logging

logger = logging.getLogger(__name__)

def exporter(*types):
    """Mark a translator method as exporting the specified item type(s)"""
    for t in types:
        if not issubclass(t,(pim.Stamp, schema.Item)) or t is pim.Stamp:
            raise TypeError("%r is not a `schema.Item` or `pim.Stamp` subclass"
                % (t,)
            )
    def decorate(func):
        func.__dict__.setdefault('_eim_exporter_for',[]).extend(types)
        return func
    return decorate

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

class IncompatibleTypes(TypeError):
    """An item's existing type can't be changed to the requested type"""


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


def typedef(alias, typeinfo):
    """Register `alias` as an alias for `typeinfo`

    `alias` may be any object.  `typeinfo` must be a type context, i.e.,
    ``typeinfo_for()`` should return a ``TypeInfo`` for it.  (Which means it
    can be a ``TypeInfo``, a URI, or a registered alias, field, etc.)
    An error occurs if `alias` is already registered."""
    typeinfo = typeinfo_for(typeinfo)   # unaliases and validates typeinfo
    typeinfo_for.when_object(alias)(lambda context: typeinfo)


@typeinfo_for.when_type(str)
def lookup_ti_by_uri(context):
    ti = lookupSchemaURI(context)
    if ti is None:
        return typeinfo_for.default(context)
    return typeinfo_for(ti)



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
        registerURI(uri, self, None)
        self.uri = uri

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


uri_registry = WeakValueDictionary()

def registerURI(uri, ob, message="A URI must be provided"):
    if uri is None:
        if message:
            raise TypeError(message)
        else:
            return
    elif uri_registry.setdefault(uri, ob) is not ob:
        raise TypeError("URI %r is already in use" % (uri,))

def lookupSchemaURI(uri, default=None):
    """Look up a filter, record type, or field type by URI"""
    return uri_registry.get(uri,default)



class DecimalType(TypeInfo):
    abstract = False
    __slots__ = ('digits', 'decimal_places')

    def __init__(self, uri=None, digits=None, decimal_places=0):
        if digits is None or decimal_places is None:
            raise TypeError(
                "digits and decimal_places must be specified when creating"
                " a sharing." + self.__class__.__name__
            )
        self.digits = digits
        self.decimal_places = decimal_places
        TypeInfo.__init__(self, uri)

    def __repr__(self):
        return 'sharing.%s(%r, %d, %d)' % (
            self.__class__.__name__, self.uri, self.digits, self.decimal_places
        )

    def clone(self, uri=None, digits=None, decimal_places=None, *args, **kw):
        if digits is None:
            digits = self.digits
        if decimal_places is None:
            decimal_places = self.decimal_places
        return self.__class__(uri, digits, decimal_places, *args, **kw)


class BytesType(SizedType): __slots__ = ()
class TextType(SizedType):  __slots__ = ()
class IntType(TypeInfo):    __slots__ = ()
class DateType(TypeInfo):   __slots__ = ()
class TimestampType(TypeInfo):   __slots__ = ()
class BlobType(TypeInfo):    __slots__ = ()
class ClobType(TypeInfo):    __slots__ = ()

# define aliases so () is optional for anonymous unsized field types
[typedef(t, t()) for t in IntType, BlobType, ClobType, DateType, TimestampType]




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









class RecordSet(object):
    """Collection of "positive" and "negative" records"""

    def __init__(self, inclusions=(), exclusions=()):
        self._index, self.inclusions, self.exclusions = {}, set(), set()
        if inclusions or exclusions:
            self.update(inclusions, exclusions)
    def __repr__(self):
        return "RecordSet(%r, %r)" % (self.inclusions, self.exclusions)
    def __eq__(self, other):
        return (
            isinstance(other, RecordSet) and self.inclusions==other.inclusions
            and self.exclusions==other.exclusions
        )

    def __ne__(self, other):
        return not self==other

    def update(self, inclusions, exclusions, subtract=False):
        ind = self._index
        for r in inclusions:
            if r is NoChange: continue
            k = r.getKey()
            if k in ind:
                ind[k] += r
            else:
                ind[k] = r
        for r in exclusions:
            if r is NoChange: continue
            k = r.getKey()
            if k in ind:
                r = ind[k] - r
                if r is NoChange or not subtract:
                    del ind[k]
                    continue
                else:
                    ind[k] = r
            else:
                self.exclusions.add(r)
        self.inclusions = set(ind.values())

    def __sub__(self, other):
        rs = RecordSet(self.inclusions, self.exclusions)
        rs.update(other.exclusions, other.inclusions, subtract=True)
        return rs

    def __add__(self, other):
        rs = RecordSet(self.inclusions, self.exclusions)
        rs.update(other.inclusions, other.exclusions)
        return rs

    def __iadd__(self, other):
        self.update(other.inclusions, other.exclusions)
        return self

    def __nonzero__(self):
        return bool(self.inclusions or self.exclusions)

    def remove(self, other):
        if isinstance(other, RecordSet):
            inclusions, exclusions = other.inclusions, other.exclusions
        else:
            inclusions, exclusions = [other], ()
        
        ind = self._index
        for r in inclusions:
            k = r.getKey()
            if k in ind:
                r = ind[k] - r
                if r is NoChange:
                    del ind[k]
                else:
                    ind[k] = r
            else:
                raise KeyError(r)
        self.inclusions = set(ind.values())

        skip = set([r.getKey() for r in exclusions])
        self.exclusions = set(
            [r for r in self.exclusions if r.getKey() not in skip]
        )
                
    def _merge(self, inclusions, exclusions):
        exc = dict((r.getKey(),r) for r in self.exclusions)
        ind = self._index
        conflicts = set()

        for r in inclusions:
            k = r.getKey()
            if k in conflicts:
                continue
            if k in exc:
                conflicts.add(k)
                del exc[k]
            elif k in ind:
                r = ind[k] | r
                if r is NoChange:
                    conflicts.add(k)
                    del ind[k]
                else:
                    ind[k] = r
            else:
                ind[k] = r

        for r in exclusions:
            k = r.getKey()
            if k in conflicts:
                continue
            if k in ind:
                conflicts.add(k)
                del ind[k]
            else:
                exc[k] = r

        self.inclusions = set(ind.values())
        self.exclusions = set(exc.values())

    def __or__(self, other):
        rs = RecordSet()
        rs._merge(self.inclusions|other.inclusions,
                 self.exclusions|other.exclusions)
        return rs

''' Partial sketch of a dependency-ordering routine

def sort_records(records):
    """Sort an iterable of records such that dependencies occur first"""
    waiting = {}
    seen = {}

    def release(key):
        seen[key] = True
        to_release = [key]
        while to_release:
            key = to_release.pop()
            if key not in waiting:
                continue
            for deps, record in waiting[key]:
                deps.remove(key)
                if not deps:
                    yield record
                    to_release.append(record.getKey())
            del waiting[key]

    for record in records:
        deps = []
        pair = deps, record
        for dep in record.requiresKeys():
            if dep not in seen:
                waiting.setdefault(dep,[]).append(pair)
        if deps:
            continue    # can't process record with outstanding dependencies

        yield record    # allow the record to pass, then its dependents
        for record in release(r.getKey()):
            yield record

    while waiting:
        for key in list(waiting):
            if key not in seen:     # release only unseen root dependencies
                for record in release(key):
                    yield record
'''

class Filter:
    """Suppress inclusion of specified field(s) in Records and RecordSets"""

    def __init__(self, uri, description):
        registerURI(uri, self, None)
        self.uri = uri
        self.description = description
        self.fields = set()
        self.types = {RecordSet: self.filter_rs}

    def __repr__(self):
        return "Filter(%r, %r)" % (self.uri, self.description)

    def filter_rs(self, recordset):
        return RecordSet(
            map(self.sync_filter, recordset.inclusions), recordset.exclusions
        )

    def __iadd__(self, other):
        if isinstance(other, field):
            flist = [other]
        elif isinstance(other, Filter):
            flist = other.fields
        else:
            raise TypeError("Can't add %r to Filter" % (other,))

        for f in flist:
            if f.owner in self.types:
                del self.types[f.owner]
            self.fields.add(f)

        return self









    def sync_filter(self, record_or_set):
        try:
            # Lookup cached filter function by type
            ff = self.types[type(record_or_set)]

        except KeyError:
            # No cached filter function, build one or use default

            t = type(record_or_set)
            if not isinstance(t, RecordClass):
                # Only record types allowed!
                raise TypeError(
                    "Not a Record or RecordSet: %r" % (record_or_set,)
                )

            all_fields = t.__fields__
            to_filter = frozenset(f for f in all_fields if f in self.fields)

            if to_filter:
                # Define a custom filter function
                def ff(record):
                    return t(*[
                        (NoChange if f in to_filter else record[f.offset])
                        for f in all_fields
                    ])
            else:
                # This isn't a record type we care about
                ff = _no_filtering

            self.types[t] = ff

        return ff(record_or_set)


def _no_filtering(record):
    # Fast default filter function used when the Filter doesn't apply to a type
    return record




def _constructor_for(name, cdict, fields):
    fname = "EIM-Generated Constructor for %s.%s" % (cdict['__module__'],name)
    args =', '.join(f.name for f in fields)
    conversions = ''.join(
        "\n    %s = get_converter(cls.%s)(%s)" % (f.name,f.name,f.name)
        for f in fields
    )
    nc_check = ' is '.join(f.name for f in fields if not isinstance(f,key))
    if nc_check: conversions+='\n    if '+nc_check+' is NoChange: return NoChange'
    source = (
        "def __new__(cls, %(args)s):%(conversions)s\n"
        "    return tuple.__new__(cls, (cls, %(args)s))""" % locals()
    )
    # Push the source into the linecache
    lines = source.splitlines(True)
    linecache.cache[fname] = 0, None, lines, fname
    return compile(source, fname, "exec")

class RecordClass(type):
    """Metaclass for records"""
    def __new__(meta, name, bases, cdict):
        try:
            Record
        except NameError:
            message = None  # Record itself doesn't need a URI
        else:
            message = "Record classes must have a `URI` attribute"
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
            for ff in f.filters: ff += f    # add fields to filters

        registerURI(cdict.get('URI'), cls, message)
        return cls

    def deleter(cls, func):
        func.__dict__.setdefault('_eim_deleter_for',[]).append(cls)
        return func

    def importer(cls, func):
        func.__dict__.setdefault('_eim_importer_for',[]).append(cls)
        return func




















_field_num = 1

class field(object):
    __slots__ = "owner", "name", "type", "typeinfo", "seq", "offset", "filters"

    def __init__(self, type, filters=()):
        global _field_num
        self.owner = self.name = None
        self.type = type
        self.typeinfo = typeinfo_for(type)
        self.seq = _field_num = _field_num + 1
        if filters or not hasattr(self, 'filters'):
            self.filters = filters

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


class key(field):
    """Primary key field (can't be filtered)"""
    __slots__ = filters = ()
    def __init__(self, type):
        field.__init__(self, type)


NoChange = Symbol('NoChange', __name__)
Missing = Symbol('Missing', __name__)

class Record(tuple):
    __slots__ = ()
    __metaclass__ = RecordClass

    def __repr__(self):
        r = "%s%r" % (self.__class__.__name__, self[1:])
        if r.endswith(',)'):
            return r[:-2]+')'
        return r

    def __sub__(self, other):
        t = type(self)
        if type(other) is not t:
            raise TypeError(
                '%r is not a %s record' % (other, self.__class__.__name__)
            )
        if other != self:
            res = []
            for f, new, old in zip(self.__fields__, self[1:], other[1:]):
                if isinstance(f,key):
                    if old!=new:
                        raise ValueError(
                            "Can't subtract %s %r from %s %r" %
                            (f.name, old, f.name, new)
                        )
                elif old==new:
                    res.append(NoChange)
                    continue
                res.append(new)

            return t(*res)

        return NoChange

    def __reduce__(self):
        return self[0], self[1:]


    def getKey(self):
        return (type(self),) + tuple(
            [self[f.offset] for f in self.__fields__ if isinstance(f,key)]
        )

    def __add__(self, other):
        t = type(self)
        if type(other) is not t:
            raise TypeError(
                '%r is not a %s record' % (other, self.__class__.__name__)
            )
        res = []
        for f, new, old in zip(self.__fields__, other[1:], self[1:]):
            if isinstance(f,key):
                if old!=new:
                    raise ValueError(
                        "Can't add %s %r to %s %r" %
                        (f.name, old, f.name, new)
                    )
            if new is NoChange:
                res.append(old)
            else:
                res.append(new)
        return t(*res)

    def explain(self):
        cls = type(self)
        data = [(f.__get__(self) if isinstance(f,key) else NoChange)
                for f in cls.__fields__]
        for f, value in zip(cls.__fields__, self[1:]):
            if not isinstance(f,key) and value is not NoChange:
                data[f.offset-1] = value
                yield (f.name, value, cls(*data))
                data[f.offset-1] = NoChange







    def __or__(self, other):
        t = type(self)
        if type(other) is not t:
            raise TypeError(
                '%r is not a %s record' % (other, self.__class__.__name__)
            )

        res = []

        for f, new, old in zip(self.__fields__, other[1:], self[1:]):
            if new is NoChange:
                res.append(old)
            elif old is NoChange:
                res.append(new)
            elif old==new:
                res.append(new)
            elif isinstance(f,key):
                raise ValueError(
                    "Can't merge %s %r and %s %r" % (f.name, old, f.name, new)
                )
            else:
                res.append(NoChange)

        return t(*res)

















required_translator_attrs = dict(
    version=int, URI=str, description=unicode).items()

class TranslatorClass(type):
    def __new__(meta, name, bases, cdict):
        try:
            Translator
        except NameError:
            pass    # Translator doesn't need any attributes set
        else:
            for attr,t in required_translator_attrs:
                if type(cdict.get(attr)) is not t:
                    raise TypeError(
                        "Translator classes must have a `%s` attribute of"
                        " type `%s`" % (attr, t.__name__)
                    )
            message = "Translator classes must have a `URI` attribute"

        cls = type.__new__(meta, name, bases, cdict)
        registerURI(cdict.get('URI'), cls, None)

        for regname, attrname in (
            ('importers','_eim_importer_for'), ('deleters','_eim_deleter_for'),
            ('exporters', '_eim_exporter_for'),
        ):
            reg = {}
            setattr(cls, regname, reg)
            for v in cdict.values():
                for ftype in getattr(v, attrname, ()):
                    if reg.setdefault(ftype,v) is not v:
                        raise TypeError(
                            "Multiple %s defined for %r in %r"
                            % (regname, ftype, cls)
                        )
            # Inherit registry contents from base classes
            for t in cls.__mro__[1:]:
                for k, v in t.__dict__.get(regname, {}).items():
                   reg.setdefault(k, v)
        return cls


class Translator:
    """Base class for import/export between Items and Records"""

    __metaclass__ = TranslatorClass

    def __init__(self, rv):
        self.rv = rv
        self.export_cache = {}

    def startImport(self):
        """Called before an import transaction begins"""

    def finishImport(self):
        """Called after an import transaction ends"""

    def startExport(self):
        """Called before an import transaction begins"""

    def finishExport(self):
        """Called after an import transaction ends"""
        return ()

    def importRecords(self, rs):
        for r in rs.inclusions:
            self.importRecord(r)

        for r in rs.exclusions:
            deleter = self.deleters.get(type(r))
            if deleter: deleter(self, r)

    def importRecord(self, r):
        importer = self.importers.get(type(r))
        try:
            if importer: importer(self, r)
        except:
            logger.exception("Failed to import %s", r)
            raise


    def _exportablesFor(self, item):
        yield item, object

        if isinstance(item, pim.ContentItem):
            for stamp in pim.Stamp(item).stamps:
                yield stamp, pim.Stamp




    def exportItem(self, item):
        """Export an item and its stamps, if any"""

        for item, skipType in self._exportablesFor(item):

            try:
                exporters = self.export_cache[type(item)]

            except KeyError:
                # Compute and cache the list of applicable exporters, in the
                # correct order for subsequent execution
                t = type(item)
                mro = t.__mro__
                mro = mro[:list(mro).index(skipType)]
                exporters = self.export_cache[t] = []
                for t in reversed(mro):
                    exporter = self.exporters.get(t)
                    if exporter:
                        exporters.append(exporter)

                # fall through to fast path

            for exporter in exporters:
                for record in exporter(self, item):
                    yield record

    def explainConflicts(self, rs):
        for r in rs.inclusions:
            for n,v,r in r.explain():
                yield n, v, RecordSet([r])
        for r in rs.exclusions:
            yield "Deleted", r.getKey(), RecordSet([], [r])









    # TODO: Remove this
    def loadItemByUUID(self, uuid, itype=schema.Item, **attrs):
        """Load/create/upgrade/stamp item by UUID and type, w/optional attrs"""

        if issubclass(itype, pim.Stamp):
            stamp = itype(self.loadItemByUUID(uuid, itype.targetType()))
            if not stamp.stamp_types or itype not in stamp.stamp_types:
                stamp.add()

            item = stamp    # fall through to attribute-setting below

        else:
            item = self.rv.findUUID(uuid)

            if item is None:
                # Create the item
                if isinstance(uuid, basestring):
                    uuid = UUID(uuid)
                item = itype(itsView=self.rv, _uuid=uuid)

            elif not isinstance(item, itype):
                # Upgrade its type, if compatible
                if not issubclass(itype, type(item)):
                    raise IncompatibleTypes(type(item), itype)
                else:
                    item.__class__ = itype
                    item.itsKind = itype.getKind(self.rv)

        # Set specified attributes, skipping NoChange attrs, and deleting
        # Missing attrs
        for attr, val in attrs.items():
            if val is Missing:
                if hasattr(item, attr):
                    delattr(item, attr)
            elif val is not NoChange:
                setattr(item, attr, val)

        return item





    def withItemForUUID(self, uuid, itype=schema.Item, **attrs):
        """Load/create/upgrade/stamp item by UUID and type, w/optional attrs"""

        if issubclass(itype, pim.Stamp):
            stamp = itype(self.loadItemByUUID(uuid, itype.targetType()))
            if not stamp.stamp_types or itype not in stamp.stamp_types:
                stamp.add()

            item = stamp    # fall through to attribute-setting below

        else:
            item = self.rv.findUUID(uuid)

            if item is None:
                # Create the item
                if isinstance(uuid, basestring):
                    uuid = UUID(uuid)
                item = itype(itsView=self.rv, _uuid=uuid)

            elif not isinstance(item, itype):
                # Upgrade its type, if compatible
                if not issubclass(itype, type(item)):
                    raise IncompatibleTypes(type(item), itype)
                else:
                    item.__class__ = itype
                    item.itsKind = itype.getKind(self.rv)

        # Set specified attributes, skipping NoChange attrs, and deleting
        # Missing attrs
        for attr, val in attrs.items():
            if val is Missing:
                if hasattr(item, attr):
                    delattr(item, attr)
            elif val is not NoChange:
                setattr(item, attr, val)

        def decorate(func):
            return func(item)
        return decorate


    def getUUIDForAlias(self, alias):
        return alias

    def getAliasForItem(self, item):
        return item.itsUUID.str16()








def create_default_converter(t):
    converter = generic(default_converter)
    converter.when_object(NoChange)(lambda val: val)
    converter.when_object(Missing)(lambda val: val)
    converter.when_object(None)(lambda val: val)
    get_converter.when_object(t)(lambda ctx: converter)

map(create_default_converter,
    [BytesType, TextType, IntType, DateType, TimestampType, BlobType, ClobType,
    DecimalType]
)

add_converter(IntType, int, int)
typedef(int, IntType)
add_converter(TextType, str, unicode)
add_converter(TextType, unicode, unicode)
add_converter(DateType, datetime.datetime, lambda v:v)
add_converter(TimestampType, datetime.datetime, lambda v:v)
add_converter(DecimalType, decimal.Decimal, decimal.Decimal)
add_converter(BlobType, str, unicode)
add_converter(ClobType, str, unicode)
add_converter(ClobType, unicode, unicode)




UUIDType = TextType("cid:uuid_type@osaf.us", size=36)
typedef(schema.UUID, UUIDType)

def uuid_converter(uuid):
    return str(uuid)

def item_uuid_converter(item):
    return str(item.itsUUID)

add_converter(UUIDType, UUID, uuid_converter)
add_converter(UUIDType, schema.Item, item_uuid_converter)
add_converter(UUIDType, str, unicode)



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




























