""" Bootstrapping Kind for Parcel"""

__revision__  = "$Revision$"
__date__      = "$Date$"
__copyright__ = "Copyright (c) 2003 Open Source Applications Foundation"
__license__   = "http://osafoundation.org/Chandler_0.1_license_terms.htm"

from repository.item.Item import Item
from repository.schema.Kind import Kind

class Parcel(Item):

    def setupParcels(repository):
        # @@@ bootstrapping for parcels
        itemKind = repository.find('//Schema/Core/Item')

        if not repository.find('//Parcels'):
            parcels = Item('Parcels', repository, itemKind)
            osaf = Item('OSAF', parcels, itemKind)

    setupParcels = staticmethod(setupParcels)

    def __init__(self, name, parent, kind):
        super(Parcel, self).__init__(name, parent, kind)
        self._status |= Item.SCHEMA

    def _fillItem(self, name, parent, kind, **kwds):
        super(Parcel, self)._fillItem(name, parent, kind, **kwds)
        self._status |= Item.SCHEMA
