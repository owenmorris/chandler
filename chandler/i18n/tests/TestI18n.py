import unittest
this_module = "application.tests.TestSchemaAPI"     # change this if it moves

from application import schema
from repository.persistence.RepositoryView import NullRepositoryView


"""Very basic tests to make sure message catalogs working will be 
   expanded"""

class I18nTestCase(unittest.TestCase):

    def testOSAFMessageFactory(self):
        from i18n import OSAFMessageFactory as _
        test = _("test is good %s %s") % ("one", "two")
        self.assertEqual(test, u"test is good one two")

    def testMessageFactory(self):
        from i18n import MessageFactory
        _ = MessageFactory("testDomain")

        test = _("test is good %s %s") % ("one", "two")
        self.assertEqual(test, u"test is good one two")
