""" Class used for Items of Kind Preferences
"""

__revision__  = "$Revision$"
__date__      = "$Date$"
__copyright__ = "Copyright (c) 2003 Open Source Applications Foundation"
__license__   = "http://osafoundation.org/Chandler_0.1_license_terms.htm"

from repository.item.Item import Item

class Preferences(Item):
    def __init__(self, name, parent, kind):
        Item.__init__(self, name, parent, kind)

    def getStartView(self):
        uuid = self.startView
        repository = self.getRepository()
        return repository.find(uuid)

    def setStartView(self, view):
        self.startView = view.getUUID()
        
