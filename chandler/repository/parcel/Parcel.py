""" Bootstrapping Kind for Parcel"""

__revision__  = "$Revision$"
__date__      = "$Date$"
__copyright__ = "Copyright (c) 2003 Open Source Applications Foundation"
__license__   = "http://osafoundation.org/Chandler_0.1_license_terms.htm"

from repository.item.Item import Item
from repository.schema.Kind import Kind

import logging

class Parcel(Item):

    def getLogger(cls):
        """Get the logger related to this parcel class"""

        if cls is Parcel:
            # Return the root logger for all parcels
            return logging.getLogger('Parcels')
        else:
            # If a subclass, assume the python module of this class
            # is the same as the parcel path, and the path we will
            # use to identify the logger.
            return logging.getLogger('Parcels.%s' % cls.__module__)

    getLogger = classmethod(getLogger)

    def setupParcels(repository):
        # @@@ bootstrapping for parcels
        itemKind = repository.find('//Schema/Core/Item')

        if not repository.find('//Parcels'):
            parcels = Parcel('Parcels', repository, itemKind)
            osaf = Parcel('OSAF', parcels, itemKind)

    setupParcels = staticmethod(setupParcels)

    def __init__(self, name, parent, kind):
        super(Parcel, self).__init__(name, parent, kind)
        self._status |= Item.SCHEMA
        self._setLogger()

    def _fillItem(self, name, parent, kind, **kwds):
        super(Parcel, self)._fillItem(name, parent, kind, **kwds)
        self._status |= Item.SCHEMA
        self._setLogger()

    def _setLogger(self):
        """Find the logger for this parcel, based on the parcel path.
           Set the logger on this parcel item.
        """

        # This method is called every time a python instance is created
        # as the repository loads, one for each thread that uses this
        # item. To set a special handler on a logger, do so once in the
        # relevant class or module.
        
        itemPath = repr(self.getItemPath())
        loggerPath = itemPath[2:].replace("/", ".")
        
        self.log = logging.getLogger(loggerPath)

    def startupParcel(self):
        self.log.debug("Starting the parcel...")
        
