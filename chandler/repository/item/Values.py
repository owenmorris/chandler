
__revision__  = "$Revision$"
__date__      = "$Date$"
__copyright__ = "Copyright (c) 2004 Open Source Applications Foundation"
__license__   = "http://osafoundation.org/Chandler_0.1_license_terms.htm"

from chandlerdb.util.uuid import UUID, _hash, _combine
from chandlerdb.item.item import Nil
from chandlerdb.item.ItemError import *
from repository.util.Path import Path
from repository.util.Lob import Lob
from repository.item.PersistentCollections import PersistentCollection
from repository.item.RefCollections import RefList
from repository.util.SingleRef import SingleRef
from repository.schema.TypeHandler import TypeHandler


class Values(dict):

    def __init__(self, item):

        super(Values, self).__init__()
        if item is not None:
            self._setItem(item)

    def clear(self):

        for name in self.iterkeys():
            self._setDirty(name)

        super(Values, self).clear()
        self._clearNoinherits()

    def _getItem(self):

        return self._item

    def _setItem(self, item):

        self._item = item

    def _refCount(self):

        count = 1

        for value in self.itervalues():
            if isinstance(value, ItemValue):
                count += value._refCount()
            elif isinstance(value, PersistentCollection):
                count += value._refCount()

        return count

    def _copy(self, orig, copyPolicy, copyFn):

        item = self._item
        for name, value in orig.iteritems():
            if isinstance(value, PersistentCollection):
                self[name] = value._copy((item, name, value._owner[2]),
                                         copyPolicy, copyFn)

            elif isinstance(value, ItemValue):
                value = value._copy(item, name)
                value._setItem(item, name)
                self[name] = value

            elif isinstance(value, SingleRef):
                policy = (copyPolicy or
                          item.getAttributeAspect(name, 'copyPolicy',
                                                  False, None, 'copy'))
                other = item.find(value.itsUUID)
                if other is None:
                    self[name] = value
                else:
                    copyOther = copyFn(item, other, policy)
                    if copyOther is not Nil:
                        self[name] = SingleRef(copyOther.itsUUID)

            else:
                self[name] = value

            self._copyFlags(orig, name)

    def _copyFlags(self, orig, name):

        flags = orig._getFlags(name, 0) & Values.COPYMASK
        if flags != 0:
            self._setFlags(name, flags)

    def __setitem__(self, key, value):

        if self._getFlags(key) & Values.READONLY:
            raise ReadOnlyAttributeError, (self._item, key)
        
        oldValue = self.get(key, None)
        if oldValue is not None and isinstance(oldValue, ItemValue):
            oldValue._setItem(None, None)

        return super(Values, self).__setitem__(key, value)

    def __delitem__(self, key):

        if self._getFlags(key) & Values.READONLY:
            raise ReadOnlyAttributeError, (self._item, key)

        value = self.get(key, None)
        if value is not None and isinstance(value, ItemValue):
            value._setItem(None, None)

        return super(Values, self).__delitem__(key)

    def _unload(self):

        super(Values, self).clear()
        try:
            self._flags.clear()
        except AttributeError:
            pass

    def _setFlag(self, key, flag):

        try:
            self._flags[key] |= flag
        except AttributeError:
            self._flags = { key: flag }
        except KeyError:
            self._flags[key] = flag

    def _clearFlag(self, key, flag):

        if '_flags' in self.__dict__:
            if key in self._flags:
                self._flags[key] &= ~flag

    def _setFlags(self, key, flags):

        try:
            self._flags[key] = flags
        except AttributeError:
            self._flags = { key: flags }

    def _getFlags(self, key, default=0):

        try:
            return self._flags.get(key, default)
        except AttributeError:
            return default

    def _isReadOnly(self, key):

        return self._getFlags(key) & Values.READONLY != 0

    def _isTransient(self, key):

        return self._getFlags(key) & Values.TRANSIENT != 0

    def _isDirty(self, key):

        return self._getFlags(key) & Values.DIRTY != 0

    def _isNoinherit(self, key):

        return self._getFlags(key) & Values.NOINHERIT != 0

    def _setTransient(self, key):

        self._setFlag(key, Values.TRANSIENT)

    def _setDirty(self, key):

        self._setFlag(key, Values.DIRTY)

    def _setNoinherit(self, key):

        self._setFlag(key, Values.NOINHERIT)

    def _clearTransient(self, key):

        try:
            self._flags[key] &= ~Values.TRANSIENT
        except AttributeError:
            pass

    def _getDirties(self):

        try:
            return [ key for key, flags in self._flags.iteritems()
                     if flags & Values.DIRTY ]
        except AttributeError:
            return []

    def _clearDirties(self):

        try:
            for key, flags in self._flags.iteritems():
                if flags & Values.DIRTY:
                    self._flags[key] &= ~Values.DIRTY
        except AttributeError:
            pass

    def _clearNoinherits(self):

        try:
            for key, flags in self._flags.iteritems():
                if flags & Values.NOINHERIT:
                    self._flags[key] &= ~Values.NOINHERIT
        except AttributeError:
            pass

    def _writeValues(self, itemWriter, version, withSchema, all):

        item = self._item
        kind = item._kind

        size = 0
        for name, value in self.iteritems():

            flags = self._getFlags(name)
            if flags & Values.TRANSIENT != 0:
                continue
            
            if kind is not None:
                attribute = kind.getAttribute(name, False, item)
                persist = attribute.getAspect('persist', True)
            else:
                attribute = None
                persist = True

            if not persist:
                continue
            
            if not (all or flags & Values.DIRTY != 0):
                size += itemWriter._unchangedValue(item, name)
                continue
            
            if value is Nil:
                raise ValueError, 'Cannot persist Nil'

            size += itemWriter._value(item, name, value,
                                      version, flags & Values.SAVEMASK, 
                                      withSchema, attribute)

        return size

    def _xmlValues(self, generator, withSchema, version):

        from repository.item.ItemHandler import ValueHandler
        
        item = self._item
        kind = item._kind
        view = item.itsView

        for key, value in self.iteritems():
            if kind is not None:
                attribute = kind.getAttribute(key, False, item)
            else:
                attribute = None

            if attribute is not None:
                persist = attribute.getAspect('persist', True)
            else:
                persist = True

            if persist:
                flags = self._getFlags(key)
                persist = flags & Values.TRANSIENT == 0
                flags &= Values.SAVEMASK

            if persist:
                if attribute is not None:
                    attrType = attribute.getAspect('type')
                    attrCard = attribute.getAspect('cardinality', 'single')
                    attrId = attribute.itsUUID
                else:
                    attrType = None
                    attrCard = 'single'
                    attrId = None

                attrs = {}
                if flags:
                    attrs['flags'] = str(flags)

                try:
                    ValueHandler.xmlValue(view, key, value, 'attribute',
                                          attrType, attrCard, attrId, attrs,
                                          generator, withSchema)
                except Exception, e:
                    e.args = ("while saving attribute '%s' of item %s, %s" %(key, item.itsPath, e.args[0]),)
                    raise
        return 0

    def _hashValues(self):

        item = self._item
        kind = item._kind
        view = item.itsView
        hash = 0

        names = self.keys()
        names.sort()
        
        for name in names:
            if kind is not None:
                attribute = kind.getAttribute(name, False, item)
            else:
                attribute = None

            if attribute is not None:
                persist = attribute.getAspect('persist', True)
            else:
                persist = True

            if persist:
                persist = self._getFlags(name) & Values.TRANSIENT == 0

            if persist:
                hash = _combine(hash, _hash(name))
                value = self[name]
                
                if attribute is not None:
                    attrType = attribute.getAspect('type')
                else:
                    attrType = None

                if attrType is not None:
                    hash = _combine(hash, attrType.hashValue(value))
                else:
                    hash = _combine(hash, TypeHandler.hashValue(view, value))

        return hash

    def _prepareMerge(self):

        if not hasattr(self, '_original'):
            self._original = self.copy()

        return self

    def _commitMerge(self):

        try:
            del self._original
        except AttributeError:
            pass

    def _revertMerge(self):

        try:
            self.update(self._original)
            del self._original
        except AttributeError:
            pass
        
    def _checkValue(self, logger, name, value, attrType):

        if not attrType.recognizes(value):
            logger.error('Value %s of type %s in attribute %s on %s is not recognized by type %s', value, type(value), name, self._item.itsPath, attrType.itsPath)
            return False

        return True

    def _checkCardinality(self, logger, name, value, cardType, attrCard):

        if not (value is None or isinstance(value, cardType)):
            logger.error('Value %s of type %s in attribute %s on %s is not an instance of type %s which is required for cardinality %s', value, type(value), name, self._item.itsPath, cardType, attrCard)
            return False

        return True

    def check(self):
        
        item = self._item
        logger = item.itsView.logger
        result = True

        for key, value in self.iteritems():
            try:
                attribute = item._kind.getAttribute(key, False, item)
            except AttributeError:
                logger.error('Item %s has a value for attribute %s but its kind %s has no definition for this attribute', item.itsPath, key, item._kind.itsPath)
                result = False
                continue

            attrType = attribute.getAspect('type', None)
            if attrType is not None:
                attrCard = attribute.getAspect('cardinality', 'single')
                if attrCard == 'single':
                    check = self._checkValue(logger, key, value, attrType)
                    result = result and check
                elif attrCard == 'list':
                    check = self._checkCardinality(logger, key, value,
                                                   list, 'list')
                    result = result and check
                    if check:
                        for v in value:
                            check = self._checkValue(logger, key, v, attrType)
                            result = result and check
                elif attrCard == 'dict':
                    check = self._checkCardinality(logger, key, value,
                                                   dict, 'dict')
                    result = result and check
                    if check:
                        for v in value.itervalues():
                            check = self._checkValue(logger, key, v, attrType)
                            result = result and check

        return result

    def _import(self, view):

        item = self._item
        if type(view) is not type(item.itsView):
            for key, value in self.iteritems():
                if isinstance(value, Lob):
                    item.setAttributeValue(key, value.copy(view), self)

    
    READONLY  = 0x0001         # value is read-only

    DIRTY     = 0x0100         # value is dirty
    TRANSIENT = 0x0200         # value is transient
    NOINHERIT = 0x0400         # no schema for inheriting a value
    SAVEMASK  = 0x00ff         # save these flags
    COPYMASK  = READONLY | TRANSIENT | NOINHERIT
    

class References(Values):

    def _setValue(self, name, other, otherName, **kwds):

        if name in self:
            value = self._getRef(name)
            if value is not None and value._isItem():
                value._references._removeRef(otherName, self._item)

        if other is not None:
            view = self._item.itsView
            otherView = other.itsView
            if not (otherView is view or
                    self._item._isImporting() or
                    other._isImporting()):
                if otherView._isNullView() or view._isNullView():
                    view.importItem(other)
                else:
                    raise ViewMismatchError, (self._item, other)
                    
            if otherName in other._references:
                value = other._references._getRef(otherName)
                if value is not None and value._isItem():
                    value._references._removeRef(name, other)

        self._setRef(name, other, otherName, **kwds)
        if other is not None:
            other._references._setRef(otherName, self._item, name,
                                      cardinality=kwds.get('otherCard'),
                                      alias=kwds.get('otherAlias'),
                                      noMonitors=kwds.get('noMonitors', False))

    def _addValue(self, name, other, otherName, **kwds):

        kwds['cardinality'] = 'list'
        self._setValue(name, other, otherName, **kwds)

    def _setRef(self, name, other, otherName, **kwds):

        item = self._item
        value = self.get(name)
        if value is None:
            cardinality = (kwds.get('cardinality') or
                           item.getAttributeAspect(name, 'cardinality',
                                                   True, None, 'single'))
            if cardinality == 'list':
                self[name] = value = item._refList(name, otherName)
            elif cardinality != 'single':
                raise CardinalityError, (item, name, 'list or single')

        if value is not None and value._isRefList():
            value._setRef(other, **kwds)
        else:
            self[name] = other
            if not item.itsView.isLoading():
                item.setDirty(item.VDIRTY, name, self,
                              kwds.get('noMonitors', False))

    def _getRef(self, name, other=None, attrID=None):

        value = self.get(name, self)
        item = self._item

        if other is None:
            if value is self:
                raise KeyError, name
            if value is None or value._isItem() or value._isRefList():
                return value
            if value._isUUID():
                other = item.find(value)
                if other is None:
                    raise DanglingRefError, (item, name, value)
                self[name] = other
                kind = item.itsKind
                if kind is not None:  # kind may be None during bootstrap
                    other._references._getRef(kind.getOtherName(name, attrID,
                                                                item), item)
                return other

            raise TypeError, '%s, type: %s' %(value, type(value))

        if value is other:
            if value._isUUID():
                other = item.find(value)
                if other is None:
                    raise DanglingRefError, (item, name, value)
                self[name] = other
            return other

        if value is self or value is None:
            raise BadRefError, (item, name, value, other)

        if value == other._uuid:
            self[name] = other
            return other

        if value._isRefList() and other in value:
            return other

        raise BadRefError, (item, name, value, other)
    
    def _removeValue(self, name, other, otherName):

        self._removeRef(name, other)
        if not (other is None or other._isRefList()):
            other._references._removeRef(otherName, self._item)

    def _removeRef(self, name, other):

        value = self.get(name, self)
        if value is self:
            raise AssertionError, '_removeRef: no value for %s' %(name)

        if value is other:
            if other is not None and other._isRefList():
                other.clear()
                self._item.setDirty(self._item.RDIRTY, name, self, True)
            else:
                self._item.setDirty(self._item.VDIRTY, name, self, True)
            del self[name]
        elif value._isUUID() and other._isItem() and value == other._uuid:
            self._item.setDirty(self._item.VDIRTY, name, self, True)
            del self[name]
        elif value._isRefList():
            value._removeRef(other)
        else:
            raise BadRefError, (self._item, name, other, value)
        
    def _unloadValue(self, name, other, otherName):

        if other is not None:
            self._unloadRef(name, other, otherName)
            if other._isItem():
                other._references._unloadRef(otherName, self._item, name)

    def _unloadRef(self, name, other, otherName):

        if not (other is None or other._isUUID()):
            value = self[name]
            if value._isRefList():
                value._unloadRef(other)
            elif value is other:
                self[name] = other._uuid
            elif value._isUUID() and value == other._uuid:
                pass
            else:
                raise BadRefError, (self._item, name, other, value)

    def clear(self):

        item = self._item
        for name in self.keys():
            item.removeAttributeValue(name, _attrDict=item._references)

    def _setItem(self, item):

        self._item = item

        for value in self.itervalues():
            if value is not None and value._isRefList():
                value._setItem(item)

    def refCount(self, loaded):

        count = 0

        for value in self.itervalues():
            if value is not None:
                if value._isItem():
                    count += 1
                elif value._isRefList():
                    count += value.refCount(loaded)
                elif not loaded and value._isUUID():
                    count += 1

        return count

    def _refCount(self):

        count = 1

        for value in self.itervalues():
            if value is not None:
                if value._isItem():
                    count += 1
                elif value._isRefList():
                    count += value._refCount()

        return count

    # copy a ref from self into copyItem._references
    def _copyRef(self, copyItem, name, other, policy, copyFn):

        value = self._getRef(name, other)
        copyOther = copyFn(copyItem, value, policy)

        if copyOther is not Nil and name not in copyItem._references:
            copyItem._references._setValue(name, copyOther,
                                           copyItem._kind.getOtherName(name))

    # copy orig._references into self
    def _copy(self, orig, copyPolicy, copyFn):

        item = self._item
        for name, value in orig.iteritems():
            policy = copyPolicy or item.getAttributeAspect(name, 'copyPolicy')
            if value is not None and value._isRefList():
                value._copy(item, name, policy, copyFn)
            else:
                orig._copyRef(item, name, value, policy, copyFn)
            self._copyFlags(orig, name)

    def _unload(self):

        for name, value in self.iteritems():
            if value is not None:
                if value._isRefList():
                    value._unload()
                elif value._isItem():
                    otherName = self._item.itsKind.getOtherName(name)
                    self._unloadValue(name, value, otherName)

        super(References, self)._unload()

    def _isRefList(self, name):

        try:
            value = self[name]
            return value is not None and value._isRefList()
        except KeyError:
            return False

    def _xmlRef(self, name, other, generator, withSchema, version, attrs,
                previous=None, next=None, alias=None):

        def addAttr(attrs, attr, value):

            if value is not None:
                if isinstance(value, UUID):
                    attrs[attr + 'Type'] = 'uuid'
                    attrs[attr] = value.str64()
                elif isinstance(attr, str) or isinstance(attr, unicode):
                    attrs[attr] = value.encode('utf-8')
                elif isinstance(attr, Path):
                    attrs[attr + 'Type'] = 'path'
                    attrs[attr] = str(value).encode('utf-8')
                else:
                    raise TypeError, "%s, type: %s" %(value, type(value))

        attrs['type'] = 'uuid'

        addAttr(attrs, 'name', name)
        addAttr(attrs, 'previous', previous)
        addAttr(attrs, 'next', next)
        addAttr(attrs, 'alias', alias)

        if withSchema:
            otherName = self._item._kind.getOtherName(name)
            otherCard = other.getAttributeAspect(otherName, 'cardinality',
                                                 False, None, 'single')
            attrs['otherName'] = otherName
            if otherCard != 'single':
                attrs['otherCard'] = otherCard
            uuid = other._uuid
        elif other._isUUID():
            uuid = other
        else:
            uuid = other._uuid

        generator.startElement('ref', attrs)
        generator.characters(uuid.str64())
        generator.endElement('ref')

    def _writeValues(self, itemWriter, version, withSchema, all):

        item = self._item
        kind = item._kind

        size = 0
        for name, value in self.iteritems():

            flags = self._getFlags(name)
            if flags & Values.TRANSIENT != 0:
                continue
            
            if kind is not None:
                attribute = kind.getAttribute(name, False, item)
                persist = attribute.getAspect('persist', True)
            else:
                attribute = None
                persist = True

            if not persist:
                continue
            
            if not (all or flags & Values.DIRTY != 0):
                size += itemWriter._unchangedValue(item, name)
                continue
            
            if value is Nil:
                raise ValueError, 'Cannot persist Nil'

            if withSchema and value is not None and value._isUUID():
                value = self._getRef(name, value)

            size += itemWriter._ref(item, name, value,
                                    version, flags & Values.SAVEMASK, 
                                    withSchema, attribute)

        return size

    def _xmlValues(self, generator, withSchema, version):

        item = self._item
        kind = item._kind

        for name, value in self.iteritems():
            attribute = kind.getAttribute(name, False, item)
            if attribute.getAspect('persist', True):
                flags = self._getFlags(name) & Values.SAVEMASK
                attrs = { 'id': attribute.itsUUID.str64() }
                if flags:
                    attrs['flags'] = str(flags)

                if value is None:
                    attrs['name'] = name
                    attrs['type'] = 'none'
                    generator.startElement('ref', attrs)
                    generator.endElement('ref')
                else:
                    if withSchema and value._isUUID():
                        value = self._getRef(name, value)
                    
                    if value._isRefList():
                        value._xmlValue(name, item, generator, withSchema,
                                        version, attrs)
                    else:
                        self._xmlRef(name, value, generator, withSchema,
                                     version, attrs)

        return 0

    def _hashValues(self):

        item = self._item
        kind = item._kind
        view = item.itsView
        hash = 0

        names = self.keys()
        names.sort()

        for name in names:
            attribute = kind.getAttribute(name, False, item)
            if attribute.getAspect('persist', True):
                hash = _combine(hash, _hash(name))
                value = self[name]
                
                if value is None:
                    hash = _combine(hash, 0)
                elif value._isUUID():
                    hash = _combine(hash, value._hash)
                elif value._isItem():
                    hash = _combine(hash, value._uuid._hash)
                elif value._isRefList():
                    hash = _combine(hash, value._hashValues())

        return hash

    def _clearDirties(self):

        super(References, self)._clearDirties()
        # clearing according to flags is not enough, flags not set on new items
        for value in self.itervalues():
            if value is not None and value._isRefList():
                value._clearDirties()

    def _commitMerge(self):

        try:
            del self._original
        except AttributeError:
            pass

        try:
            dirties = self._dirties
            del self._dirties
        except AttributeError:
            dirties = None

        for key, value in self.iteritems():
            if value is not None and value._isRefList():
                if dirties is not None and key in dirties:
                    value._clear_()
                else:
                    try:
                        del value._original
                    except AttributeError:
                        pass

    def _revertMerge(self):

        try:
            original = self._original
            self.update(original)
            del self._original
        except AttributeError:
            original = self

        try:
            del self._dirties
        except AttributeError:
            pass

        for key, value in original.iteritems():
            try:
                if value is not None and value._isRefList():
                    self[key] = value._original
                    del value._original
            except AttributeError:
                pass

    def _checkRef(self, logger, name, other):

        if other is not None:
            if not other._isItem():
                other = self._item.find(other)
                if other is None:
                    logger.error('DanglingRefError: %s.%s',
                                 self._item.itsPath, name)
                    return False

            if other.isStale():
                logger.error('Found stale item %s at %s.%s',
                             other, self._item.itsPath, name)
                return False

            if other.itsView is not self._item.itsView:
                logger.error("views don't match: %s at %s.%s",
                             other, self._item.itsPath, name)
                return False

        otherName = self._item._kind.getOtherName(name, None, None, None)
        if otherName is None:
            logger.error('otherName is None for attribute %s.%s',
                         self._item._kind.itsPath, name)
            return False

        if other is not None:
            if other._kind is None:
                raise AssertionError, 'no kind for %s' %(other.itsPath)
            otherOtherName = other._kind.getOtherName(otherName,
                                                      None, None, None)
            if otherOtherName != name:
                logger.error("otherName for attribute %s.%s, %s, does not match otherName for attribute %s.%s, %s",
                             self._item._kind.itsPath, name, otherName,
                             other._kind.itsPath, otherName, otherOtherName)
                return False

            otherOther = other._references._getRef(otherName)
            if not (otherOther is self._item or
                    otherOther._isRefList() and self._item in otherOther):
                if otherOther._isRefList():
                    logger.error("%s doesn't contain a reference to %s, yet %s.%s references %s",
                                 otherOther, other._repr_(), other._repr_(),
                                 otherName, self._item._repr_())
                else:
                    logger.error("%s.%s doesn't reference %s.%s but %s",
                                 other._repr_(), otherName, self._item._repr_(),
                                 name, otherOther)
                return False

        return True

    def check(self):

        from repository.item.Item import Item

        item = self._item
        logger = item.itsView.logger
        result = True

        for key, value in self.iteritems():
            if value is not None and value._isUUID():
                value = self._getRef(key, value)
                
            attrCard = item.getAttributeAspect(key, 'cardinality',
                                               False, None, 'single')
            if attrCard == 'single':
                check = self._checkCardinality(logger, key, value,
                                               Item, 'single')
                if check:
                    check = self._checkRef(logger, key, value)
            elif attrCard == 'list':
                check = self._checkCardinality(logger, key, value,
                                               RefList, 'list')
                if check:
                    check = value.check(logger, key, item)
            elif attrCard == 'dict':
                logger.error("Attribute %s on %s is using deprecated 'dict' cardinality, use 'list' instead", key, self._item.itsPath)
                check = value.check(logger, key, item)
                check = False
                
            result = result and check

        return result

    def _import(self, view, items, replace):

        item = self._item
        itemView = item.itsView
        sameType = type(view) is type(itemView)

        for key, value in self.items():
            if value is not None:
                if value._isRefList():
                    if sameType or value._isTransient():
                        previous = None
                        for other in value:
                            if other not in items:
                                alias = value.getAlias(other)
                                value.remove(other)
                                localOther = other.findMatch(view, replace)
                                if localOther is not None:
                                    value.insertItem(localOther, previous)
                                    if alias is not None:
                                        value.setAlias(other, alias)
                    else:
                        localValue = view._createRefList(item, value._name, value._otherName, True, False, True, UUID())
                        value._copyIndexes(localValue)
                        for other in value:
                            if other in items:
                                localValue._setRef(other, load=True,
                                                   alias=value.getAlias(other),
                                                   noMonitors=True)
                            else:
                                value.remove(other)
                                localOther = other.findMatch(view, replace)
                                if localOther is not None:
                                    localValue.append(localOther,
                                                      value.getAlias(other))
                        item._references[key] = localValue
                else:
                    if value._isUUID():
                        value = itemView.find(value)
                    if value not in items:
                        localOther = value.findMatch(view, replace)
                        item.removeAttributeValue(key)
                        if localOther is not None:
                            item.setAttributeValue(key, localOther)


class ItemValue(object):
    'A superclass for values that are owned by an item.'
    
    def __init__(self):

        self._item = None
        self._attribute = None
        self._dirty = False
        self._readOnly = False

    def _setItem(self, item, attribute):

        if item is not None:
            if self._item is not None and self._item is not item:
                raise OwnedValueError, (self._item, self._attribute, self)
        
        self._item = item
        self._attribute = attribute

    def _setReadOnly(self, readOnly=True):

        self._readOnly = readOnly
        
    def _getItem(self):

        return self._item

    def _refCount(self):

        return 1

    def _getAttribute(self):

        return self._attribute

    def _isReadOnly(self):

        return self._readOnly and self._item is not None

    def _setDirty(self):

        if self._isReadOnly():
            raise ReadOnlyAttributeError, (self._item, self._attribute)

        self._dirty = True
        item = self._item
        if item is not None:
            item.setDirty(item.VDIRTY, self._attribute, item._values)

    def _copy(self, item, attribute):

        raise NotImplementedError, '%s._copy' %(type(self))
