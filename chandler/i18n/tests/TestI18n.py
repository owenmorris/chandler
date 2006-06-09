import unittest
this_module = "i18n.tests.TestI18n"     # change this if it moves


"""Very basic tests to make sure message catalogs are working. This will be 
   expanded"""

class I18nTestCase(unittest.TestCase):

    def testOSAFMessageFactory(self):
        from i18n import OSAFMessageFactory as _
        import i18n

        i18nMan = i18n._I18nManager
        i18nMan.setLocaleSet(['en'])

        test = _(u"\u00FCtest is good %s %s") % ("one", "two")
        self.assertEqual(test, u"\u00FCtest is good one two")

    def testMessageFactory(self):
        from i18n import MessageFactory
        import i18n
        _ = MessageFactory("testDomain")

        i18nMan = i18n._I18nManager
        i18nMan.setLocaleSet(['en'])

        test = _(u"\u00FCtest is good %s %s") % ("one", "two")
        self.assertEqual(test, u"\u00FCtest is good one two")

if __name__ == "__main__":
    unittest.main()
