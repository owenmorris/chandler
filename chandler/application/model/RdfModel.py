#!bin/env python

"""Base classes for RDF objects in Chandler
"""

__author__ = "Katie Capps Parlante"
__version__ = "$Revision$"
__date__ = "$Date$"
__copyright__ = "Copyright (c) 2002 Open Source Applications Foundation"
__license__ = "Python"

from application.persist import Persist

class ObservableItem:
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
    
class RdfObject(object, Persist.Persistent):
    """Base class for any RDF model object in Chandler"""
    
    def __init__(self):
        Persist.Persistent.__init__(self)
    

    
