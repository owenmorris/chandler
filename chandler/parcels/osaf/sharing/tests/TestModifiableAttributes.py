import unittest
from osaf import pim, sharing
from util import testcase

class TestModifiableAttributes(testcase.NRVTestCase):

    def testModifiable(self):

        view = self.view

        # Our test subject
        e1 = pim.CalendarEvent(itsView=view)

        # Add the subject to a read-only share:

        share_ro = sharing.Share(itsView=view)
        share_ro.mode = 'get'

        e1.sharedIn.append(share_ro)

        # Test modifiability against...

        # ...an attribute which is always shared
        self.assert_(not e1.isAttributeModifiable('displayName'))

        # ...an attribute that is sometimes shared (based on filterAttributes)
        self.assert_(not e1.isAttributeModifiable('reminders'))

        # ...an attribute which is pretty much never shared
        self.assert_(e1.isAttributeModifiable('read'))

        # Filter out reminderTime, and it should become modifiable:
        share_ro.filterAttributes = ['reminders']
        self.assert_(e1.isAttributeModifiable('reminders'))

        # Now also add the subject to a read-write share:

        share_rw = sharing.Share(itsView=view)
        share_rw.mode = 'both'

        e1.sharedIn.append(share_rw)

        # Test modifiability against...

        # ...an attribute which is always shared
        self.assert_(e1.isAttributeModifiable('displayName'))

        # ...an attribute that is sometimes shared (based on filterAttributes)
        self.assert_(e1.isAttributeModifiable('reminders'))

        # ...an attribute which is pretty much never shared
        self.assert_(e1.isAttributeModifiable('read'))

if __name__ == "__main__":
    unittest.main()
