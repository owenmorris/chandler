
__revision__  = "$Revision$"
__date__      = "$Date$"
__copyright__ = "Copyright (c) 2004 Open Source Applications Foundation"
__license__   = "http://osafoundation.org/Chandler_0.1_license_terms.htm"

from chandlerdb.util.UUID import UUID
from repository.util.Path import Path
from repository.item.PersistentCollections import PersistentCollection
from repository.item.RefCollections import RefList
from repository.item.ItemError import *
from repository.util.SingleRef import SingleRef


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
                self[name] = value._copy(item, name, value._companion,
                                         copyPolicy, copyFn)

            elif isinstance(value, ItemValue):
                value = value._copy(item, name)
                value._setItem(item, name)
                self[name] = value

            elif isinstance(value, SingleRef):
                policy = (copyPolicy or
                          item.getAttributeAspect(name, 'copyPolicy',
                                                  default='copy'))
                other = item.find(value.itsUUID)
                copyOther = copyFn(item, other, policy)

                if copyOther is not None:
                    self[name] = SingleRef(copyOther.itsUUID)
            else:
                self[name] = value

    def __setitem__(self, key, value):

        if self._getFlags(key) & Values.READONLY:
            raise ReadOnlyAttributeError, (self._item, key)

        return super(Values, self).__setitem__(key, value)

    def __delitem__(self, key):

        if self._getFlags(key) & Values.READONLY:
            raise ReadOnlyAttributeError, (self._item, key)

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

    def _isMonitored(self, key):

        return self._getFlags(key) & Values.MONITORED != 0

    def _isDirty(self, key):

        return self._getFlags(key) & Values.DIRTY != 0

    def _isNoinherit(self, key):

        return self._getFlags(key) & Values.NOINHERIT != 0

    def _setTransient(self, key):

        self._setFlag(key, Values.TRANSIENT)

    def _setMonitored(self, key):

        self._setFlag(key, Values.MONITORED)

    def _setDirty(self, key):

        self._setFlag(key, Values.DIRTY)

    def _setNoinherit(self, key):

        self._setFlag(key, Values.NOINHERIT)

    def _clearTransient(self, key):

        try:
            self._flags[key] &= ~Values.TRANSIENT
        except AttributeError:
            pass

    def _clearMonitored(self, key):

        try:
            self._flags[key] &= ~Values.MONITORED
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

        all = True

        for name, value in self.iteritems():

            flags = self._getFlags(name)
            if not (all or flags & Values.DIRTY != 0):
                continue
            
            if kind is not None:
                attribute = kind.getAttribute(name)
                persist = attribute.getAspect('persist', default=True)
            else:
                attribute = None
                persist = True

            if not (persist and flags & Values.TRANSIENT == 0):
                continue
            
            if value is item.Nil:
                raise ValueError, 'Cannot persist Item.Nil'

            itemWriter._value(item, name, value,
                              version, flags & Values.SAVEMASK, 
                              withSchema, attribute)

    def _xmlValues(self, generator, withSchema, version):

        from repository.item.ItemHandler import ValueHandler
        
        item = self._item
        kind = item._kind
        repository = item.itsView

        for key, value in self.iteritems():
            if kind is not None:
                attribute = kind.getAttribute(key)
            else:
                attribute = None

            if attribute is not None:
                persist = attribute.getAspect('persist', default=True)
            else:
                persist = True

            if persist:
                flags = self._getFlags(key)
                persist = flags & Values.TRANSIENT == 0
                flags &= Values.SAVEMASK

            if persist:
                if attribute is not None:
                    attrType = attribute.getAspect('type')
                    attrCard = attribute.getAspect('cardinality',
                                                   default='single')
                    attrId = attribute.itsUUID
                else:
                    attrType = None
                    attrCard = 'single'
                    attrId = None

                attrs = {}
                if flags:
                    attrs['flags'] = str(flags)

                try:
                    ValueHandler.xmlValue(repository, key, value, 'attribute',
                                          attrType, attrCard, attrId, attrs,
                                          generator, withSchema)
                except Exception, e:
                    e.args = ("while saving attribute '%s' of item %s, %s" %(key, item.itsPath, e.args[0]),)
                    raise

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
            logger._error('Value %s of type %s in attribute %s on %s is not recognized by type %s', value, type(value), name, self._item.itsPath, attrType.itsPath)
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
                attribute = item._kind.getAttribute(key)
            except AttributeError:
                logger.error('Item %s has a value for attribute %s but its kind %s has no definition for this attribute', item.itsPath, key, item._kind.itsPath)
                result = False
                continue

            attrType = attribute.getAspect('type', default=None)
            if attrType is not None:
                attrCard = attribute.getAspect('cardinality', default='single')
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

    
    READONLY  = 0x0001         # value is read-only
    MONITORED = 0x0002         # value is monitored
    DIRTY     = 0x0100         # value is dirty
    TRANSIENT = 0x0200         # value is transient
    NOINHERIT = 0x0400         # no schema for inheriting a value
    SAVEMASK  = 0x00ff         # save these flags


class References(Values):

    def _setValue(self, name, other, otherName, **kwds):

        if name in self:
            value = self._getRef(name)
            if value is not None and value._isItem():
                value._references._removeRef(otherName, self._item)

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
                                                   noError=True,
                                                   default='single'))
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

    def _getRef(self, name, other=None):

        value = self.get(name, self)

        if other is None:
            if value is self:
                raise KeyError
            if value is None:
                return value
            if value._isUUID():
                other = self._item.find(value)
                if other is None:
                    raise DanglingRefError, (self._item, name, value)
                self[name] = other
                if self._item.itsKind is None:
                    raise AssertionError, '%s: no kind' %(self._item.itsPath)
                other._references._getRef(self._item.itsKind.getOtherName(name),
                                          self._item)
                return other
            if value._isRefList() or value._isItem():
                return value
            raise TypeError, '%s, type: %s' %(value, type(value))

        if value is other:
            if value._isUUID():
                other = self._item.find(value)
                if other is None:
                    raise DanglingRefError, (self._item, name, value)
            self[name] = other
            return other

        if value is self or value is None:
            raise BadRefError, (self._item, name, value, other)

        if value == other._uuid:
            self[name] = other
            return other

        if value._isRefList() and other in value:
            return other

        raise BadRefError, (self._item, name, value, other)
    
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

        if copyOther is not copyItem.Nil and name not in copyItem._references:
            copyItem._references._setValue(name, copyOther,
                                           copyItem._kind.getOtherName(name))

    # copy orig._references into self
    def _copy(self, orig, copyPolicy, copyFn):

        item = self._item
        for name, value in orig.iteritems():
            policy = copyPolicy or item.getAttributeAspect(name, 'copyPolicy')
            if value is not None:
                if value._isRefList():
                    value._copy(item, name, policy, copyFn)
                else:
                    orig._copyRef(item, name, value, policy, copyFn)

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
                                                 default='single')
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

        all = True

        for name, value in self.iteritems():

            flags = self._getFlags(name)
            if not (all or flags & Values.DIRTY != 0):
                continue
            
            if kind is not None:
                attribute = kind.getAttribute(name)
                persist = attribute.getAspect('persist', default=True)
            else:
                attribute = None
                persist = True

            if not (persist and flags & Values.TRANSIENT == 0):
                continue
            
            if value is item.Nil:
                raise ValueError, 'Cannot persist Item.Nil'

            if withSchema and value is not None and value._isUUID():
                value = self._getRef(name, value)

            itemWriter._ref(item, name, value,
                            version, flags & Values.SAVEMASK, 
                            withSchema, attribute)

    def _xmlValues(self, generator, withSchema, version):

        item = self._item
        kind = item._kind

        for name, value in self.iteritems():
            attribute = kind.getAttribute(name)
            if attribute.getAspect('persist', default=True):
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
            if dirties is not None and key in dirties:
                if value is not None and value._isRefList():
                    value._clear_()
            else:
                try:
                    if value is not None and value._isRefList():
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

        otherName = self._item._kind.getOtherName(name, default=None)
        if otherName is None:
            logger.error('otherName is None for attribute %s.%s',
                         self._item._kind.itsPath, name)
            return False

        if other is not None:
            if other._kind is None:
                raise AssertionError, 'no kind for %s' %(other.itsPath)
            otherOtherName = other._kind.getOtherName(otherName, default=None)
            if otherOtherName != name:
                logger.error("otherName for attribute %s.%s, %s, does not match otherName for attribute %s.%s, %s",
                             self._item._kind.itsPath, name, otherName,
                             other._kind.itsPath, otherName, otherOtherName)
                return False

            otherOther = other._references._getRef(otherName)
            if not (otherOther is self._item or
                    otherOther._isRefList() and self._item in otherOther):
                logger.error("%s.%s doesn't reference %s.%s",
                             other.itsPath, otherName, self._item.itsPath, name)
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
                                               default='single')
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
        

class ItemValue(object):
    'A superclass for values that are owned by an item.'
    
    def __init__(self):

        self._item = None
        self._attribute = None
        self._dirty = False
        self._readOnly = False

    def _setItem(self, item, attribute):

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
