__version__ = "$Revision$"
__date__ = "$Date$"
__copyright__ = "Copyright (c) 2002 Open Source Applications Foundation"
__license__ = "http://osafoundation.org/Chandler_0.1_license_terms.htm"

from repository.schema.AutoItem import AutoItem

class ParcelV2 (AutoItem):
    """
      The abstract base class for all parcels. All parcels must include
    an __init__.py something like:
        
    parcelV2Class = "MrMenus.MrMenus"

    The application uses newParcelClass to know the class the parcel implements
    and calls the class method Install to install the parcel
    """

 
