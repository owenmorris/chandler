__author__ = "John Anderson"
__version__ = "$Revision$"
__date__ = "$Date$"
__copyright__ = "Copyright (c) 2002 Open Source Applications Foundation"
__license__ = "OSAF License"

from persistence import Persistent

class Parcel (Persistent):
    """
      The abstract base class for all parcels. All parcels must include
    an __init__.py something like:
        
    from parcels.buttons import Buttons
    parcelClass = Buttons.Buttons

    The application uses parcelClass to know the class the parcel implements
    and calls the class method Install to install the parcel as follows:
    
    def Install(theClass):
        # Your installation code specific to your parcel goes here. See
        # ViewerParcel for an example
    Install = classmethod (Install)
    """

 
