import unittest
this_module = "application.tests.TestSchemaAPI"     # change this if it moves

from application import schema
from repository.packs.chandler.Types import LocalizableString
from repository.persistence.RepositoryView import NullRepositoryView

class I18nTestCase(unittest.TestCase):
    """Reset the schema API between unit tests"""

    def testLocalizableString(self):
        ls = LocalizableString("testdomain", u"test %s string %s")

        self.assertEqual(ls._domain, "testdomain")
        self.assertEqual(ls._defaultText, u"test %s string %s")
        self.assertEqual(ls._args, None)

        ls % ("one", u"two")
        self.assertEqual(ls._args, ("one", u"two"))

        us = unicode(ls)

        self.assertEqual(us, u"test one string two")
 
        # nake sure the args were reset to None and the
        # defaultText is unchanged
        self.assertEqual(ls._defaultText, u"test %s string %s")
        self.assertEqual(ls._args, None)


