"""Event Management API -- see 'events.txt' for documentation"""

from types import MethodType
from weakref import ref

__all__ = ['EventClass', 'Event', 'weak_sender', 'weak_receiver']

class EventClass(type):
    """Metaclass for event classes; handles subscription implementation"""

    def __init__(cls,name,bases,cdict):
        cls._receivers = {}

    def subscribe(cls,sender,receiver,hold=False):
        """Call `receiver` with events of this type from `sender`

        If `hold` is true, then a reference to `receiver` will be held until
        `sender` is garbage-collected.  (Normally, only a weak reference to
        `receiver` will be kept, if possible.)
        """
        sender_id = id(sender)
        if hold:
            rcv = receiver
        else:
            # Keep weak receiver in a separate variable, so receiver can't
            # get GC'd before we finish
            rcv = weak_receiver(
                receiver, lambda ref:cls._unsubscribe(sender_id,rcv)
            )

        if sender_id in cls._receivers:
            # Don't create another weak sender if one's already registered
            cls._receivers[sender_id].add(rcv)
            return

        ws = weak_sender(sender, lambda ref: cls._unsubscribe(ws,None))

        # setdefault here is for thread-safety, in case two threads
        # add a subscriber for the same sender (i.e., it's not guaranteed
        # that 'sender_id not in cls._receivers' still holds at this point)
        cls._receivers.setdefault(ws,set()).add(rcv)


    def unsubscribe(cls,sender,receiver):
        """Stop sending events of this type from `sender` to `receiver`"""
        cls._unsubscribe(id(sender),receiver)


    def _unsubscribe(cls,sender_id,receiver):
        try:
            receivers = cls._receivers[sender_id]
        except KeyError:
            return
        if receiver is None:
            receivers.clear()
            del cls._receivers[sender_id]
            return
        try:
            receivers.remove(receiver)
        except KeyError:
            pass
        try:
            receivers.remove(weak_receiver(receiver))
        except KeyError:
            pass

class Event:
    """Base class for event types"""

    __metaclass__ = EventClass

    __slots__ = 'sender', 'consumed'

    def __init__(self,sender,**args):
        self.sender = sender
        self.consumed = False
        for k,v in args.items():
            setattr(self,k,v)
        for rcv in list(self.getReceivers(sender)):
            if self.consumed:
                break
            rcv(self)

    def __setattr__(self,attr,value):
        if attr.startswith('_') or not hasattr(type(self),attr):
            raise TypeError("%r is not a public attribute of %r objects"
                % (attr,type(self).__name__))
        super(Event,self).__setattr__(attr,value)
                
    @classmethod
    def getReceivers(cls,sender):
        return cls._receivers.get(id(sender),())


class weak_sender(int):
    """Pointer-like wrapper for senders"""

    __slots__ = 'ref'

    def __new__(cls, sender, callback=None):
        """Return a pointer-like wrapper for `sender`

        Returns an object that hashes and compares equal to ``id(sender)``,
        as long as `sender` is a live object.  `callback` is called with a
        weak reference when `sender` is garbage collected, unless `sender` is
        not weak-referenceable.  (In which case, the ``weak_sender`` instance
        will hold a reference to ``sender`` until the ``weak_sender`` is itself
        garbage collected.
        """
        self = int.__new__(cls,id(sender))
        try:
            self.ref = ref(sender,callback)
        except TypeError:
            self.ref = lambda: sender
        return self

    def __eq__(self,other):
        return self is other or int(self)==other and self.ref() is not None


class weak_receiver(ref):
    """Garbage-collectable call wrapper for receivers"""

    func = None

    def __new__(cls, receiver, callback=None):
        """Return a garbage-collectable wrapper for `receiver`

        If `receiver` is weak-referenceable, `callback` will be called with a
        weak reference when the `receiver` is garbage collected.  Special
        handling for transient object methods is included."""

        if isinstance(receiver,MethodType):
            try:
                self = ref.__new__(cls,receiver.im_self,callback)
            except TypeError:
                return receiver
            else:
                self.func = receiver.im_func
                return self

        try:
            return ref.__new__(cls,receiver,callback)
        except TypeError:
            return receiver

    def __eq__(self,other):
        return super(weak_receiver,self).__eq__(other) and \
            self.func==getattr(other,'func',self.func)

    def __call__(self,*args,**kw):
        try:
            referent = ref.__call__(self)
            if referent is not None:
                if self.func is not None:
                    return self.func(referent,*args,**kw)
                else:
                    return referent(*args,**kw)
        finally:
            referent = None

