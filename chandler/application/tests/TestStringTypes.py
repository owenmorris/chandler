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
        
    def testLocalizableString(self):
        item = self.manager.lookup(STRING_PARCEL, "LocalizableStringItem")
        value = item.localizableString
        self.failUnless(isinstance(value, LocalizableString))

        self.failUnless(hasattr(value, 'defaultText'))
        self.failIf(isinstance(value.defaultText, str))
        self.failUnless(isinstance(value.defaultText, unicode))
        self.failUnlessEqual(value.defaultText,
                u"S'il vous plait -- localizez-moi!")
        self.failIfEqual(unicode(value), "")

        #self.failUnlessEqual(unicode(value), u"S'il vous plait -- localizez-moi!")
        
    def testUStringText(self):
        item = self.manager.lookup(STRING_PARCEL, "UStringTextItem")
        value = item.text
        self.failUnless(isinstance(value, unicode))
        self.failIf(isinstance(value, str))
        self.failUnlessEqual(value, u"I should be a UString")
        
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

    def testTextWithoutType(self):
        item = self.manager.lookup(STRING_PARCEL, "TextItem")
        value = item.text
        #import pdb; pdb.set_trace()
        self.failUnless(isinstance(value, LocalizableString))

        self.failUnless(hasattr(value, 'defaultText'))
        self.failIf(isinstance(value.defaultText, str))
        self.failUnless(isinstance(value.defaultText, unicode))
        self.failUnlessEqual(value.defaultText,
            "I am a Text, but should be localizable")
        self.failIfEqual(unicode(value), u"")

