#!bin/env python

"""Mixin class implementing the observer/observable pattern
"""

__version__ = "$Revision$"
__date__ = "$Date$"
__copyright__ = "Copyright (c) 2002 Open Source Applications Foundation"
__license__ = "OSAF"

class Observable:
    """Mixin class, used to make an object observable"""
    def __init__(self):
        self._observerList = []
        
    def registerObserver(self, observer):
        self._observerList.append(observer)
        
    def removeObserver(self, observer):
        if observer in self._observerList :
            self._observerList.remove(observer)
    
    def notifyObservers(self):
        for observer in self._observerList :
            observer.notify(self)    
    

    
