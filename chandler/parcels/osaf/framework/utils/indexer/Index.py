__version__ = "$Revision$"
__date__ = "$Date$"
__copyright__ = "Copyright (c) 2003 Open Source Applications Foundation"
__license__ = "http://osafoundation.org/Chandler_0.1_license_terms.htm"

from repository.item.Item import Item

class Index(Item):
    def __init__(self, *args, **kwds):
        super(Index, self).__init__(*args, **kwds)
        self.items = []
    def addItem(self, item):
        self.addValue('items', item)
    def removeItem(self, item):
        self.removeValue('items', item)
    def hasItem(self, item):
        return self.hasValue('items', item)
