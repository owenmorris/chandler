__revision__  = "$Revision$"
__date__      = "$Date$"
__copyright__ = "Copyright (c) 2003 Open Source Applications Foundation"
__license__   = "http://osafoundation.org/Chandler_0.1_license_terms.htm"

import application.Globals as Globals
import OSAF.framework.utils.indexer as indexer
from repository.item.Item import Item

class Event(Item):
    def __init__(self, *args):
        super(Event, self).__init__(*args)
        indexer.getIndex('events').addItem(self)
