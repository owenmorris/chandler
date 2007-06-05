#   Copyright (c) 2003-2007 Open Source Applications Foundation
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


# Import classes whose schemas are part of this parcel
# (this should include all ContentItem subclasses in this package)
#
"""
See proxy.txt for reStructuredText documentation.
"""

__all__ = (
    'UserChangeProxy', 'RecurrenceProxy',
    'CHANGE_ALL', 'CHANGE_THIS', 'CHANGE_FUTURE'
)

import application.schema as schema
import items
import stamping
import mail
import reminders
from calendar.Calendar import EventStamp
from chandlerdb.util.c import Nil
import inspect

class SimpleValue(object):
    def __init__(self, descriptor):
        self.descriptor = descriptor
        
    def getValue(self, proxy):
        if proxy is None: # I am the class attribute, really.
            return self

        changes = proxy.changes or []
        
        for thisChange in reversed(changes):
            if thisChange[0] is self:
                if thisChange[1] == 'delete':
                    if hasattr(self.descriptor, 'defaultValue'):
                        return self.descriptor.defaultValue
                    else:
                        raise AttributeError, self.descriptor.name
                else:
                    assert thisChange[1] == 'set'
                    return thisChange[3]
        return getattr(proxy.proxiedItem, self.descriptor.name)
            
    def setValue(self, obj, value):
        oldValue = getattr(obj, self.descriptor.name, self) # self is a cheat
        oldTz = getattr(oldValue, 'tzinfo', None)
        newTz = getattr(value, 'tzinfo', None)
        
        if oldValue != value or oldTz != newTz:
            obj.appendChange(self, 'set', self.descriptor.name, value)
        
    def deleteValue(self, obj):
        obj.appendChange(self, 'delete', self.descriptor.name)
        
    def set(self, item, name, value):
        setattr(item, name, value)
        return 1
        
    def delete(self, item, name):
        delattr(item, name)
        return 1

class Container(object):
    def __init__(self, descriptor, proxy):
        self.descriptor = descriptor
        self.proxy = proxy
        
    def __iter__(self):
        values = None
        added = set()
        removed = set()
        
        for change in reversed(self.proxy.changes or []):
            if change[0] is self.descriptor:
                if change[1].startswith('add'):
                    added.add(change[2])
                elif change[1].startswith('remove'):
                    removed.add(change[2])
                elif change[1] == 'clear':
                    values = ()
                    break
                elif change[1] == 'set':
                    values = ()
                    break
                    
        if values is None:
            values = getattr(self.proxy.proxiedItem, self.descriptor.descriptor.name, ())
            
        for value in values:
            if not value in removed:
                yield value
                
        for value in added:
            if not value in values:
                yield value
                
    def __nonzero__(self):
        for i in self.__iter__():
            return True
        return False
        
    def __len__(self):
        return sum(1 for x in self)
                
    def first(self):
        try:
            return self.__iter__().next()
        except StopIteration:
            return None

    def union(self, iterable):
        return set(itertools.chain(iterable, iter(self)))

    def add(self, val):
        self.proxy.appendChange(self.descriptor, 'add', val)
        
    def remove(self, val):
        self.proxy.appendChange(self.descriptor, 'remove', val)

    def clear(self):
        self.proxy.appendChange(self.descriptor, 'clear') #?
        

class MultiValue(SimpleValue):
    containerFactory = Container
    
    def getValue(self, ob, typ=None):
        if ob is None:
            return self
            
        if ob.containers is None:
            ob.containers = {}
            
        result = ob.containers.get(self.descriptor.name, None)
        
        if result is None:
            result = ob.containers[self.descriptor.name] = self.containerFactory(self, ob)
            
        return result 

    def add(self, obj, val):
        existing = getattr(obj, self.descriptor.name)
        if not val in existing:
            existing.add(val)
            return 1
        else:
            return 0
        
    def remove(self, obj, val):
        existing = getattr(obj, self.descriptor.name)
        if val in existing:
            existing.remove(val)
            return 1
        else:
            return 0
        getattr(obj, self.descriptor.name).remove(val)
        
    def clear(self, obj):
        existing = getattr(obj, self.descriptor.name)
        existing.clear()
        return self


class StampContainer(Container):
    def add(self, val):
        self.proxy.appendChange(self.descriptor, 'addStamp', val)
        
    def remove(self, val):
        self.proxy.appendChange(self.descriptor, 'removeStamp', val)
    
class StampTypesValue(MultiValue):
    containerFactory = StampContainer

    def addStamp(self, item, val):
        val(item).add() 
        return 1  
        
    def removeStamp(self, item, val):
        val(item).remove()
        return 1
        

class MethodWrapper(object):
    def __init__(self, method):
        func = method.im_func
        
        def getValue(proxy):
            def f(*args, **kw):
                return func(proxy, *args, **kw)
            f.__name__ = method.__name__
            return f
        
        self.getValue = getValue

class UserChangeProxy(object):
    """
    A L{UserChangeProxy} object is what's used to detect changes in the
    Chandler UI, and.
    
    """
    
    proxiedItem = None
    isProxy = True
    changes = None
    containers = None
    
    @property
    def __class__(self):
        return self.proxiedItem.__class__

    def __eq__(self, other):
        return self.proxiedItem == getattr(other, 'proxiedItem', other)

    def __ne__(self, other):
        return self.proxiedItem != getattr(other, 'proxiedItem', other)

    def __repr__(self):
        return "<%s at 0x%x for %r>" % (type(self).__name__, id(self),
                                        self.proxiedItem)

    _repr_ = __repr__

    def __str__(self):
        return "<%s at 0x%x for %s>" % (type(self).__name__, id(self),
                                        self.proxiedItem)


    def __new__(proxyClass, itemOrAnnotation):
        if isinstance(itemOrAnnotation, schema.Annotation):
            annotationClass = type(itemOrAnnotation)
            return annotationClass(proxyClass(itemOrAnnotation.itsItem))

        item = getattr(itemOrAnnotation, 'proxiedItem', itemOrAnnotation)

        if reminders.isDead(itemOrAnnotation):
            return None
        
        return object.__new__(proxyClass, item)

    def __init__(self, item):
        """
        For example:
        
        >>> item = items.ContentItem(itsView=view)
        >>> UserChangeProxy(item)
        <UserChangeProxy object at 0x...>
        
        A C{UserChangeProxy} can only be created on a L{items.ContentItem}:
        >>> UserChangeProxy("hello")
        Traceback (most recent call last):
        ...
        TypeError: Can't proxy a non-ContentItem hello
        >>>
        """
        if not isinstance(item, items.ContentItem):
            raise TypeError, "Can't proxy a non-ContentItem %s" % (item,)
        
        self.proxiedItem = item
        
    def __getValueWrapper(self, attr):
    
        for change in self.changes or []:
            # See if we have a change pending for this attribute
            if change[2] == attr:
                return change[0]
    
        target = self.proxiedItem.__class__
        descriptor = getattr(target, attr, None)
        
        if descriptor is None and attr.find(".") != -1:
            try:
                descriptor = schema.importString(attr)
            except ImportError:
                pass

        if isinstance(descriptor, schema.Descriptor):
            if attr == stamping.Stamp.stamp_types.name:
                attrStore = StampTypesValue(descriptor)
            elif getattr(descriptor, 'cardinality', 'single') == 'single':
                attrStore = SimpleValue(descriptor)
            else:
                attrStore = MultiValue(descriptor)
        elif isinstance(descriptor, schema.Calculated):
            attrStore = SimpleValue(descriptor)
        elif inspect.ismethod(descriptor):
            attrStore = MethodWrapper(descriptor)
        else:
            return None
        return attrStore
        
    def __setattr__(self, attr, value):
        attrStore = self.__getValueWrapper(attr)
        
        if attrStore is not None:
            attrStore.setValue(self, value)
        else:
            object.__setattr__(self, attr, value)

    def __getattr__(self, attr):
        attrStore = self.__getValueWrapper(attr)
        
        if attrStore is not None:
            return attrStore.getValue(self)
        else:
            return getattr(self.proxiedItem, attr)
            
    def __delattr__(self, attr):
        attrStore = self.__getValueWrapper(attr)
        
        if attrStore is not None:
            attrStore.deleteValue(self)
        else:
            object.__delattr__(self, attr)

    def appendChange(self, *args):
        assert len(args) >= 3
        if self.changes is None:
            self.changes = []
        self.changes.append(args)

    def markEdited(self, item):
        me = item.getCurrentMeEmailAddress()
        who = None # We will mark this message as "edited by" this user.
    
        if stamping.has_stamp(item, mail.MailStamp):
            # For Mail items, we want to update the From: address to match
            # something in the user's list of addresses (Bug 8534).
            message = mail.MailStamp(item)
            meAddresses = mail.getCurrentMeEmailAddresses(item.itsView)
            sender = message.getSender()
            
            if sender in meAddresses:
                # Already addressed by this user; don't need to do
                # anything more here.
                who = sender
            else:
                # Try to find a matching recipient; any field will do
                # (so far as arguments to getRecipients() go, we've already
                # preferentially included the sender, but should still check
                # originators & bcc) 
                for recipient in message.getRecipients():
                    if recipient in meAddresses:
                        who = recipient
                        break
                else:
                    # No match in for loop; use the current "me" address
                    who = me
                # OK, update the from address
                message.fromAddress = who
                    
        if who is None:
            who = item.getMyModifiedByAddress()

        item.changeEditState(who=who)
    

    def makeChanges(self):
        count = 0
        
        changes = self.changes or []
        cls = type(self)
        
        if changes:
            del self.changes
        
        for thisChange in changes:
            method = getattr(thisChange[0], thisChange[1])
            count += method(self.proxiedItem, *thisChange[2:])
            
        if count > 0:
            self.markEdited(self.proxiedItem)
        return count
        
    def cancel(self):
        if self.changes is not None:
            del self.changes

class Changer(object):
    def __new__(cls, *args):
        self = object.__new__(cls)
        factory = lambda x:x
        
        if not args:
            return self # just an empty instance
            
        itemOrAnnotation = args[0]
        
        if isinstance(itemOrAnnotation, schema.Annotation):
            factory = type(itemOrAnnotation)
            item = itemOrAnnotation.itsItem
        else:
            item = itemOrAnnotation
        
        if reminders.isDead(item):
            return None

        if item.isProxy:
            self.proxy = type(item)(item.proxiedItem)
        else:
            self.proxy = RecurrenceProxy(item)

        self.proxy.changing = cls

        return factory(self.proxy)
    
    def makeChange(self, item, change):
        return 0

class CHANGE_THIS(Changer):
    """
    Subclass to support making "THIS" changes to recurring event series. You
    use it via something like:
    
        obj = CHANGE_THIS(event) # Pass in an Annotation, Stamp or Item
        
        event.startTime = ... # Makes a THIS change to startTime
        TaskStamp(event).add() ... # adds task-ness to just this instance
    """
        
    def makeChange(self, item, change):
        event = EventStamp(item)
        changeType = change[1]
        if changeType == 'set':
            EventStamp(item).changeThis(change[2], change[3])
        elif changeType in ('addStamp', 'removeStamp'):
            event.changeThis()
            method = getattr(change[0], change[1])
            return method(item, *change[2:])
        elif changeType == 'add' and change[2] is schema.ns("osaf.pim", item.itsView).trashCollection:
            event.deleteThis()
        elif changeType in ('add', 'remove'):
            assert False, "Changing collections of a single instance is not supported"
            return 0
        return 1

class CHANGE_ALL(Changer):
    """
    Subclass to support making "ALL" changes to recurring event series. You
    use it via something like:
    
        obj = CHANGE_ALL(event) # Pass in an Annotation, Stamp or Item
        
        event.startTime = ... # Change all startTimes in the recurring series
        TaskStamp(event).add() ... # adds task-ness to all events in the series
    """
    def makeChange(self, item, change):
        # easy for set, not too bad for stamp addition, del is maybe
        # tricky, and add/remove require duplicating reflists
        event = EventStamp(item)
        changeType = change[1]
        if changeType == 'set':
            event.changeAll(change[2], change[3])
        elif changeType == 'addStamp':
            event.addStampToAll(change[2])
        elif changeType == 'removeStamp':
            event.removeStampFromAll(change[2])
        elif changeType == 'add' and change[2] is schema.ns("osaf.pim", item.itsView).trashCollection:
            event.deleteAll()
        elif changeType in ('add', 'remove'):
            masterItem = event.getMaster().itsItem
            ref = getattr(masterItem, change[0].descriptor.name)
            method = getattr(ref, changeType)
            method(change[2])
        else:
            assert False
            return 0

        return 1
        
class CHANGE_FUTURE(Changer):
    """
    Subclass to support making "THISANDFUTURE" changes to recurring event series.
    (In the current implementation, this will create a new master if the
    chosen occurrence isn't the first). You use it via something like:
    
        obj = CHANGE_FUTURE(event) # Pass in an Annotation, Stamp or Item
        
        event.startTime = ... # Change all future startTimes in the recurring series
        TaskStamp(event).add() ... # adds task-ness to all future events in the series
    """
    
    def makeChange(self, item, change):
        event = EventStamp(item)
        changeType = change[1]
        # as above, for CHANGE_ALL
        if changeType == 'set':
            event.changeThisAndFuture(change[2], change[3])
        elif changeType == 'addStamp':
            event.changeThisAndFuture()
            event.addStampToAll(change[2])
        elif changeType == 'removeStamp':
            event.changeThisAndFuture()
            event.removeStampFromAll(change[2])
        elif changeType == 'add' and change[2] is schema.ns("osaf.pim", item.itsView).trashCollection:
            event.deleteThisAndFuture()
        elif changeType in ('add', 'remove'):
            event.changeThisAndFuture()
            masterItem = event.getMaster().itsItem
            ref = getattr(masterItem, change[0].descriptor.name)
            method = getattr(ref, changeType)
            method(change[2])
        else:
            assert False
            return 0

        return 1

class RecurrenceProxy(UserChangeProxy):
    """
    A C{UserChangeProxy} that understands how to delay changes for
    recurring changes.
    
    The C{changing} attribute is used to control whether or not changes are
    propagated to the actual proxied item. The default behaviour, C{None},
    causes changes to be save, and not propagated.  When it is set to a
    subclass (not a subclass instance) of C{Changer}, changes will be propagated
    immediately via that class's C{makeChange} method.
    """
    
    changing = None
    
    def makeChanges(self):
        count = 0
        
        if self.changing and self.changes:
            changer = self.changing()
            
            for change in self.changes:
                count += changer.makeChange(self.proxiedItem, change)
                
            del self.changes
            
        if count > 0:
            self.markEdited(EventStamp(self.proxiedItem).getMaster().itsItem)
            
        return count
        
    def appendChange(self, desc, op, attr, *args):
        super(RecurrenceProxy, self).appendChange(desc, op, attr, *args)
        item = self.proxiedItem

        if (not stamping.has_stamp(item, EventStamp) or
            EventStamp(item).rruleset is None):
            super(RecurrenceProxy, self).makeChanges()
        elif self.changing is not None:
            self.makeChanges()
            
    def cancel(self):
        super(RecurrenceProxy, self).cancel()
        if self.changing is not None:
            del self.changing

