
__revision__  = "$Revision$"
__date__      = "$Date$"
__copyright__ = "Copyright (c) 2002 Open Source Applications Foundation"
__license__   = "http://osafoundation.org/Chandler_0.1_license_terms.htm"


import threading


class ThreadLocal(object):
    """A class using thread local storage for its attributes.

    All attributes on this class have thread local values."""
    
    __slots__ = ()
    

    def __getattr__(self, name):

        try:
            return self._getCurrentThreadLocals()[name]
        except KeyError:
            raise AttributeError, name

    def __setattr__(self, name, value):

        self._getCurrentThreadLocals()[name] = value

    def __delattr__(self, name):

        try:
            del self._getCurrentThreadLocals()[name]
        except KeyError:
            raise AttributeError, name

    def _getCurrentThreadLocals(self):

        currentThread = threading.currentThread()

        try:
            threadLocals = currentThread.threadLocals[self]

        except AttributeError:
            threadLocals = {}
            currentThread.threadLocals = { self: threadLocals }

        except KeyError:
            currentThread.threadLocals[self] = threadLocals = {}

        return threadLocals
