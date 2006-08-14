import unittest
import wx
import i18n
import os
from i18n import *
from i18n.i18nmanager import *
from i18n import wxMessageFactory as w

this_module = "i18n.tests.TestI18n"

class I18nTestCase(unittest.TestCase):
    PROJECT = u"Chandler.i18n_test"
    IMG_DIR = u"imgs.test.resources"
    HTML_DIR = u"html.test.resources"
    CATALOG  = u"test.catalog"
    INI_FILE = u"resources_test.ini"
    LOCALE_SET = ["fr_CA", "es_UY"]

    def setUp(self):
        # A wx application instance must be created
        # before using the wx translation API's
        self.app = wx.App()

        self.i18nMan = i18n._I18nManager

        self.i18nMan._DEFAULT_PROJECT = self.PROJECT
        self.i18nMan._DEFAULT_CATALOG = self.CATALOG
        self.i18nMan._DEFAULT_IMAGE = self.IMG_DIR
        self.i18nMan._DEFAULT_HTML = self.HTML_DIR

        self.i18nMan.initialize(self.LOCALE_SET, self.INI_FILE)
        self.mf = MessageFactory(self.PROJECT, self.CATALOG)

    def testWxMessageFactory(self):
        self.assertEquals(w("Cancel"), u"Annuler")
        self.assertEquals(w("&Quit"), u"&Quitter")

        self.i18nMan.setLocaleSet("es_UY")
        self.assertEquals(w("Cancel"), u"Cancelar")
        self.assertEquals(w("&Quit"), u"&Salir")

        self.i18nMan.setLocaleSet("en")
        self.assertEquals(w("Cancel"), u"Cancel")
        self.assertEquals(w("&Quit"), u"&Quit")

        # The 'test' locale is a debug keyword
        # which sets the locale set to ['fr_CA', 'fr']
        # and enables the testing mode flag.
        # In testing mode all values returned by
        # the WxMessageFactory method insert
        # a (WX)\u00FC: at the start of the string.
        self.i18nMan.setLocaleSet("test")
        self.assertEquals(w("Cancel"), u"(WX)\u00FC: Annuler")
        self.assertEquals(w("&Quit"), u"(WX)\u00FC: &Quitter")

        # Restore the default locale set
        self.i18nMan.setLocaleSet(self.LOCALE_SET)


    def testChandlerMessageFactory(self):
        """
            This is a simple test to ensure that
            the ChandlerMessageFactory returns
            the correct default values when no
            localizations are found for the given
            key.

           The testMessageFactory method does
           actual confirmation of localized values
           retrieved from gettext .mo files.
        """

        from i18n import ChandlerMessageFactory as cmf

        txt = cmf(u"\u00FCtest is good")
        self.assertEqual(txt, u"\u00FCtest is good")

    def testMessageFactory(self):
        txt = self.mf(u"Hello")
        self.assertEquals(txt, u"Bonjour")

        txt = self.mf(u"NO_VALUE")
        self.assertEquals(txt, u"NO_VALUE")

        self.i18nMan.setLocaleSet([u"es_UY", u"fr_CA"])

        txt = self.mf(u"Hello")
        self.assertEquals(txt, u"Hola")

        self.i18nMan.setLocaleSet("en")

        txt = self.mf(u"Hello")
        self.assertEquals(txt, u"Hello")

        # The 'test' locale is a debug keyword
        # which sets the locale set to ['fr_CA', 'fr']
        # and enables the testing mode flag.
        # In testing mode all values returned by
        # the I18nManager.getText method insert
        # a (\u00FC): at the start of the string.

        self.i18nMan.setLocaleSet("test")
        txt = self.mf(u"Hello")
        self.assertEquals(txt, u"(\u00FC): Bonjour")

        # Restore the default locale set
        self.i18nMan.setLocaleSet(self.LOCALE_SET)

    def testGetImage(self):

        # From the 'fr' locale
        img = self.i18nMan.getImage("test.png")
        self.assert_(img is not None)

        # From the 'fr' locale
        img = self.i18nMan.getImage("test2.png")
        self.assert_(img is not None)

        # From the 'all' default
        img = self.i18nMan.getImage("test1.png")
        self.assert_(img is not None)

        img = self.i18nMan.getImage("bogus.png")
        self.assert_(img is None)

        #reset to spanish with fr_CA fallback
        self.i18nMan.setLocaleSet([u"es_UY", u"fr_CA"])

        # From the 'fr' locale
        img = self.i18nMan.getImage("test2.png")
        self.assert_(img is not None)

        # From the 'fr' locale
        img = self.i18nMan.getImage("test.png")
        self.assert_(img is not None)

        # From the 'all' default
        img = self.i18nMan.getImage("test1.png")
        self.assert_(img is not None)

        #reset to spanish with English fallback
        self.i18nMan.setLocaleSet([u"es_UY", u"en_US"])

        # Only in the 'fr' locale which is no longer in the
        # locale set
        img = self.i18nMan.getImage("test2.png")
        self.assert_(img is None)

        # From the 'all' default
        img = self.i18nMan.getImage("test.png")
        self.assert_(img is not None)

        #then english
        self.i18nMan.setLocaleSet("en")

        # From the 'all' default
        img = self.i18nMan.getImage("test1.png")
        self.assert_(img is not None)

        # Restore the default locale set
        self.i18nMan.setLocaleSet(self.LOCALE_SET)

        # Test with non-default values
        i18nMan = I18nManager(i18n.CHANDLER_PROJECT,
                              i18n.DEFAULT_CATALOG,
                              i18n.DEFAULT_IMAGE,
                              i18n.DEFAULT_HTML)

        i18nMan.initialize(self.LOCALE_SET, self.INI_FILE)

        # From the 'all' default
        img = i18nMan.getImage("test1.png", self.PROJECT,
                               self.IMG_DIR)
        self.assert_(img is not None)

        img = i18nMan.getImage("test1.png", self.PROJECT,
                               "BAD_PATH")
        self.assert_(img is None)


    def _getHTML(self, file_name, project=None, html_dir=None,
                 i18nMan=None):

        if i18nMan is None:
            i18nMan = self.i18nMan

        """ Converts an str stream to unicode """
        htmlStream = i18nMan.getHTML(file_name, project,
                                     html_dir)

        if htmlStream:
            buffer = ""

            for line in htmlStream:
                buffer += line

            return unicode(buffer, "UTF-8")

        return None


    def testGetHTML(self):

        html = self._getHTML("test.html")
        self.assert_(u"French test\u00FC" in html)

        html = self._getHTML("test2.html")
        self.assert_(u"French test\u00FC for test 2" in html)

        html = self._getHTML("test3.html")
        self.assert_(u"Spanish test\u00FC for 3" in html)

        # From the 'all' default
        html = self._getHTML("test1.html")
        self.assert_(u"This is a test\u00FC for 1" in html)

        #reset to spanish with fr_CA fallback
        self.i18nMan.setLocaleSet([u"es_UY", u"fr_CA"])

        html = self._getHTML("test3.html")
        self.assert_(u"Spanish test\u00FC for 3" in html)

        html = self._getHTML("test2.html")
        self.assert_(u"Spanish test\u00FC for 2" in html)

        # From the 'all' default
        html = self._getHTML("test1.html")
        self.assert_(u"This is a test\u00FC for 1" in html)

        html = self._getHTML("test.html")
        self.assert_(u"French test\u00FC" in html)

        #reset to spanish no fallback
        self.i18nMan.setLocaleSet(u"es_UY")

        html = self._getHTML("test3.html")
        self.assert_(u"Spanish test\u00FC for 3" in html)

        # From the 'all' default
        html = self._getHTML("test.html")
        self.assert_(u"This is a test\u00FC" in html)

        # From the 'all' default
        html = self._getHTML("test1.html")
        self.assert_(u"This is a test\u00FC for 1" in html)

        #reset to English no fallback
        self.i18nMan.setLocaleSet(u"en")

        html = self._getHTML("test3.html")
        self.assertEquals(html, None)

        html = self._getHTML("test2.html")
        self.assertEquals(html, None)

        # From the 'all' default
        html = self._getHTML("test.html")
        self.assert_(u"This is a test\u00FC" in html)

        # From the 'all' default
        html = self._getHTML("test1.html")
        self.assert_(u"This is a test\u00FC for 1" in html)

        # Restore the default locale set
        self.i18nMan.setLocaleSet(self.LOCALE_SET)

        # Test with non-default values
        i18nMan = I18nManager(i18n.CHANDLER_PROJECT,
                              i18n.DEFAULT_CATALOG,
                              i18n.DEFAULT_IMAGE,
                              i18n.DEFAULT_HTML)

        i18nMan.initialize(self.LOCALE_SET, self.INI_FILE)

        html = self._getHTML("test3.html", self.PROJECT,
                             self.HTML_DIR, i18nMan)
        self.assert_(u"Spanish test\u00FC for 3" in html)

        html = self._getHTML("test2.html", self.PROJECT,
                             self.HTML_DIR, i18nMan)
        self.assert_(u"French test\u00FC for test 2" in html)

        # From the 'all' default
        html = self._getHTML("test1.html", self.PROJECT,
                             self.HTML_DIR, i18nMan)
        self.assert_(u"This is a test\u00FC for 1" in html)


    def testSetLocaleSet(self):
        self.assertRaises(UnicodeEncodeError,
                     self.i18nMan.setLocaleSet, u"\u00FC")

        self.assertRaises(NameError,
               self.i18nMan.setLocaleSet, "bogus")

        self.assertRaises(NameError,
               self.i18nMan.setLocaleSet, ['fr', 'bogus'])

        # Restore the default locale set
        self.i18nMan.setLocaleSet(self.LOCALE_SET)

    def testSetWxLocale(self):
        self.assertRaises(I18nException,
                      setWxLocale, "bogus")

        self.assertRaises(I18nException,
                   setWxLocale, "fr_SX")

    def testSetPyICULocale(self):
        self.assertRaises(I18nException,
                      setPyICULocale, "bogus")

        self.assertRaises(I18nException,
                   setPyICULocale, "fr_SX")

    def testWxFileHandler(self):
        b = self.i18nMan.CanOpen("image:test.png")
        self.assertEquals(b, True)

        b = self.i18nMan.CanOpen("image:bogus.png")
        self.assertEquals(b, False)

        b = self.i18nMan.CanOpen("BadProject#image:test.png")
        self.assertEquals(b, False)

        b = self.i18nMan.CanOpen("Chandler.i18n_test#image:test.png")
        self.assertEquals(b, True)

        b = self.i18nMan.CanOpen("bogus:test.bogus")
        self.assertEquals(b, False)

        b = self.i18nMan.CanOpen("html:test.html")
        self.assertEquals(b, True)

        b = self.i18nMan.CanOpen("html:bogus.html")
        self.assertEquals(b, False)

        b = self.i18nMan.CanOpen("BadProject#html:test.html")
        self.assertEquals(b, False)

        b = self.i18nMan.CanOpen("Chandler.i18n_test#html:test.html")
        self.assertEquals(b, True)

        b = self.i18nMan.CanOpen("resource:test.resource")
        self.assertEquals(b, True)

        b = self.i18nMan.CanOpen("resource:bogus.resource")
        self.assertEquals(b, False)

        b = self.i18nMan.CanOpen("BadProject#resource:test.resource")
        self.assertEquals(b, False)

        b = self.i18nMan.CanOpen("Chandler.i18n_test#resource:test.resource")
        self.assertEquals(b, True)

if __name__ == "__main__":
    unittest.main()
