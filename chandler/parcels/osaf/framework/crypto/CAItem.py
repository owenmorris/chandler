__copyright__ = "Copyright (c) 2004 Open Source Applications Foundation"
__license__   = "http://osafoundation.org/Chandler_0.1_license_terms.htm"

from repository.item.Item import Item

class CAItem(Item):
    """
    Keep track of all the information that is needed to run a primitive CA.
    """
    def __init__(self, *args):
        super(CAItem, self).__init__(*args)


    

