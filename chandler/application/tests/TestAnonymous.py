"""
Anonymous item tests for Parcel Loader
"""
__revision__  = "$Revision$"
__date__      = "$Date$"
__copyright__ = "Copyright (c) 2003-2004 Open Source Applications Foundation"
__license__   = "http://osafoundation.org/Chandler_0.1_license_terms.htm"

import ParcelLoaderTestCase, os, sys, unittest
import application
from application.Parcel import Parcel as Parcel

from application.Parcel import PrintItem as PrintItem

class AnonymousTestCase(ParcelLoaderTestCase.ParcelLoaderTestCase):

    def setUp(self):
    
        super(AnonymousTestCase, self).setUp()
        self.manager.path.append(os.path.join(os.path.dirname(ParcelLoaderTestCase.__file__), 'testparcels'))
        self.loadParcels(
            ["http://testparcels.org/anonymous"]
        )
        

    def testParcel(self):
        """
        Test to ensure that defining a top-level Parcel item
        with no itsName attribute works correctly.
        """

        parcel = self.manager.lookup("http://testparcels.org/anonymous")
        
        self.assert_(parcel)
        self.assert_(isinstance(parcel, Parcel))
        self.assert_(parcel.itsName == "anonymous")
     
    def testAnonymousItem(self):
        """
        Test to ensure an anonymous item (i.e. one without an itsName
        parameter specified in parcel.xml) can be set up correctly.
        """
        item = self.manager.lookup("http://testparcels.org/anonymous",
                                   "itemWithSubItem")
        self.assert_(item)
        
        itemChildren = [child for child in item.iterChildren()]
        
        self.assert_(len(itemChildren) == 1)
        
        self.assert_(itemChildren[0].itsKind == item.itsKind)

    def testAnonymousAttributeItems(self):
        """
        Test to ensure anonymous items (i.e. items without an itsName
        parameter in parcel.xml) can be set up correctly when they are
        specified as values of an attribute.
        """

        item = self.manager.lookup("http://testparcels.org/anonymous",
                                   "itemWithAttributes")

        #PrintItem("//parcels/anonymous", self.manager.repo, recursive=True)
        
        self.assert_(item)
        
        itemChildren = [child for child in item.iterChildren()]
        self.assert_(itemChildren)
        self.assert_(len(itemChildren) == 3)
        
        attributeValue = item.myAttribute
        self.assert_(attributeValue)
        
        for key, value in attributeValue.iteritems():
            # Raise if value is not present in itemChildren 
            index = itemChildren.index(value)
            del itemChildren[index]
            
        self.assert_(itemChildren == [])


if __name__ == "__main__":
    unittest.main()
