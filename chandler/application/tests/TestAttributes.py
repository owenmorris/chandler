"""
Attribute tests for Parcel Loader
"""
__revision__  = "$Revision$"
__date__      = "$Date$"
__copyright__ = "Copyright (c) 2003-2004 Open Source Applications Foundation"
__license__   = "http://osafoundation.org/Chandler_0.1_license_terms.htm"

import ParcelLoaderTestCase, os, sys, unittest
import application
import repository.util.Lob

ATTR_PARCEL = "parcel:application.tests.testparcels.attributes"
class AttributesTestCase(ParcelLoaderTestCase.ParcelLoaderTestCase):

    def setUp(self):
    
        super(ParcelLoaderTestCase.ParcelLoaderTestCase, self).setUp()
        self.manager.path.append(os.path.join(os.path.dirname(ParcelLoaderTestCase.__file__), 'testparcels'))
        self.loadParcels([ATTR_PARCEL])
        

    def testBoolean(self):
        """
        Test to ensure a dict of Boolean-valued attributes is set correctly
        on an item by the parcel loader.
        """

        item = self.manager.lookup(ATTR_PARCEL, "booleanItem")
                                    
        self.assert_(item)
        self.assert_(isinstance(item.BooleanAttr, dict))
        self.assert_(item.BooleanAttr == {
            'true': True,
            'false': False
        })
        

    def testInt(self):
        """
        Test to ensure a list of Integer-valued attributes is set correctly
        on an item by the parcel loader.
        """
        
        item = self.manager.lookup(ATTR_PARCEL, "intItem")
        self.assert_(item)
        self.assert_(isinstance(item.IntAttr, list))
        self.assert_(len(item.IntAttr) == 2)
        self.assert_(type(item.IntAttr[0]) == int)
        self.assert_(type(item.IntAttr[1]) == int)
        self.assert_(item.IntAttr[0] == -451)
        self.assert_(item.IntAttr[1] == 99)

    def testFloat(self):
        """
        Test to ensure a single float-valued attribute is set correctly
        on an item by the parcel loader.
        """
    
        item = self.manager.lookup(ATTR_PARCEL, "floatItem")
        self.assert_(item)
        self.assert_(isinstance(item.FloatAttr, float))
        self.assert_(item.FloatAttr == -40.175)

    def testDict(self):
        """
        Test to ensure a list of Dictionary-valued attributes is set correctly
        on an item by the parcel loader.
        """

        item = self.manager.lookup(ATTR_PARCEL, "dictItem")
        self.assert_(item)
        self.assert_(isinstance(item.DictAttr, list))
        self.assert_(len(item.DictAttr) == 3)
        self.assert_(isinstance(item.DictAttr[0], dict))
        self.assert_(isinstance(item.DictAttr[1], dict))
        self.assert_(isinstance(item.DictAttr[2], dict))
        
        self.assert_(item.DictAttr[0] == {
            21: "FirstValue", True:
             ["1", "2", "3"]
         })

        self.assert_(item.DictAttr[1] == {"This": "The real life?"})
        self.assert_(item.DictAttr[2] == {})

    def testList(self):
        """
        Test to ensure a List-valued attribute is set correctly
        on an item by the parcel loader.
        """

        item = self.manager.lookup(ATTR_PARCEL, "listItem")
        self.assert_(item)
        self.assert_(isinstance(item.ListAttr, list))
        self.assert_(len(item.ListAttr) == 3)
        self.assert_(type(item.ListAttr[0]) == int)
        self.assert_(type(item.ListAttr[1]) == bool)
        self.assert_(isinstance(item.ListAttr[2], (str, unicode)))
        self.assert_(item.ListAttr[0] == 39)
        self.assert_(item.ListAttr[1] == True)
        self.assert_(item.ListAttr[2] == "Hello, cruel world")
    
    def testTuple(self):
        """
        Test to ensure a Tuple-valued attribute is set correctly
        on an item by the parcel loader.
        """

        item = self.manager.lookup(ATTR_PARCEL,  "tupleItem")
        self.assert_(item)
        self.assert_(isinstance(item.TupleAttr, tuple))
        self.assert_(item.TupleAttr == (3.25e-5, ["x", "y"]))
    
    def testString(self):
        """
        Test to ensure a list of String-valued attributes is set correctly
        on an item by the parcel loader.
        """

        item = self.manager.lookup(ATTR_PARCEL, "stringItem")
        self.assert_(item)
        self.assert_(isinstance(item.StringAttr, dict))
        self.assert_(item.StringAttr == {
                'note-one': u"\u2022 That was a bullet point",
                'note-two': u"It\u2019s such a lovely day."
            })
    
    
    def testLob(self):
        """
        Test to ensure a Lob-valued attribute is set correctly
        on an item by the parcel loader.
        """
        
        item = self.manager.lookup(ATTR_PARCEL, "lobItem")
        self.assert_(item)
        self.assert_(isinstance(item.LobAttr, repository.util.Lob.Lob))
        #@@@ Need a test of item.LobAttr's contents

if __name__ == "__main__":
    unittest.main()
