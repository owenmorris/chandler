import ParcelLoaderTestCase, os, sys, unittest
from application import schema
from repository.packs.chandler.Types import LocalizableString

STRING_PARCEL = "parcel:application.tests.testparcels.string"

class StringTestCase(ParcelLoaderTestCase.ParcelLoaderTestCase):

    def setUp(self):
        super(ParcelLoaderTestCase.ParcelLoaderTestCase, self).setUp()
        self.manager.path.append(os.path.join(os.path.dirname(ParcelLoaderTestCase.__file__), 'testparcels'))
        self.loadParcels([STRING_PARCEL])
        
    def testBString(self):
        item = self.manager.lookup(STRING_PARCEL, "BStringItem")
        value = item.bString
        
        self.failUnless(isinstance(value, str))
        self.failIf(isinstance(value, unicode))
        self.failUnlessEqual(value, "This should be a str")

    def testUString(self):
        item = self.manager.lookup(STRING_PARCEL, "UStringItem")
        value = item.uString
        
        self.failUnless(isinstance(value, unicode))
        self.failIf(isinstance(value, str))
        self.failUnlessEqual(value, u"Is this unicode?")
        
    def testUStringEscape(self):
        item = self.manager.lookup(STRING_PARCEL, "UStringEscapeItem")
        value = item.uString
        
        self.failUnless(isinstance(value, unicode))
        self.failIf(isinstance(value, str))
        self.failUnlessEqual(value, u"\u2022 Was that a bullet?")

    def testUStringRaw(self):
        item = self.manager.lookup(STRING_PARCEL, "UStringRawItem")
        value = item.uString
        
        self.failUnless(isinstance(value, unicode))
        self.failIf(isinstance(value, str))
        self.failUnlessEqual(value, u"\u2022 Was that a bullet?")
