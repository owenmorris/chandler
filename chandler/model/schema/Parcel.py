""" Bootstrapping Kind for Parcel"""

__revision__  = "$Revision$"
__date__      = "$Date$"
__copyright__ = "Copyright (c) 2003 Open Source Applications Foundation"
__license__   = "http://osafoundation.org/Chandler_0.1_license_terms.htm"

from model.schema.AutoKind import AutoKind
from model.item.Item import Item
from model.schema.Kind import Kind

class Parcel(Item, AutoKind):

    def setupParcels(repository):
        # @@@ bootstrapping for parcels
        itemKind = repository.find('//Schema/Core/Item')
        schemaContainer = repository.find('//Schema')

        parcelsContainer = Item('Parcels', repository, itemKind)

        # @@@ need to handle this more generally
        osafSchemaContainer = Item('OSAF', schemaContainer, itemKind)
        osafParcelsContainer = Item('OSAF', parcelsContainer, itemKind)

    setupParcels = staticmethod(setupParcels)

    def __init__(self, name, parent, kind):
        Item.__init__(self, name, parent, kind)
        
        repository = self.getRepository()
        stringType = repository.find('//Schema/Core/String')
        
        self.createAttribute('author', type=stringType)
        self.createAttribute('publisher', type=stringType)
        self.createAttribute('status', type=stringType)
        self.createAttribute('displayName', type=stringType)
        self.createAttribute('summary', type=stringType)
        self.createAttribute('description', type=stringType)
        self.createAttribute('icon', type=stringType)
        self.createAttribute('version', type=stringType)
