import unittest
from repository.persistence.RepositoryView import NullRepositoryView
from osaf import pim, sharing

class TestModifiableAttributes(unittest.TestCase):

    def testModifiable(self):

        view = NullRepositoryView()

        # Our test subject
        e1 = pim.CalendarEvent(view=view)

        # Add the subject to a read-only share:

        share_ro = sharing.Share(view=view)
        share_ro.mode = 'get'

        e1.sharedIn.append(share_ro)

        # Test modifiability against...

        # ...an attribute which is always shared
        self.assert_(not e1.isAttributeModifiable('displayName'))

        # ...an attribute that is sometimes shared (based on filterAttributes)
        self.assert_(not e1.isAttributeModifiable('reminderTime'))

        # ...an attribute which is pretty much never shared
        self.assert_(e1.isAttributeModifiable('read'))


        # Filter out reminderTime, and it should become modifiable:

        share_ro.filterAttributes = ['reminderTime']
        self.assert_(e1.isAttributeModifiable('reminderTime'))


        # Now also add the subject to a read-write share:

        share_rw = sharing.Share(view=view)
        share_rw.mode = 'both'

        e1.sharedIn.append(share_rw)

        # Test modifiability against...

        # ...an attribute which is always shared
        self.assert_(e1.isAttributeModifiable('displayName'))

        # ...an attribute that is sometimes shared (based on filterAttributes)
        self.assert_(e1.isAttributeModifiable('reminderTime'))

        # ...an attribute which is pretty much never shared
        self.assert_(e1.isAttributeModifiable('read'))

if __name__ == "__main__":
    unittest.main()
