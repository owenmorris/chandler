#   Copyright (c) 2003-2006 Open Source Applications Foundation
#
#   Licensed under the Apache License, Version 2.0 (the "License");
#   you may not use this file except in compliance with the License.
#   You may obtain a copy of the License at
#
#       http://www.apache.org/licenses/LICENSE-2.0
#
#   Unless required by applicable law or agreed to in writing, software
#   distributed under the License is distributed on an "AS IS" BASIS,
#   WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
#   See the License for the specific language governing permissions and
#   limitations under the License.


import unittest
from osaf import pim, sharing
from application import schema
from util import testcase
from i18n.tests import uw

class TestModifiableAttributes(testcase.NRVTestCase):

    def testModifiable(self):

        view = self.view

        # Our test subject
        e1 = pim.CalendarEvent(itsView=view)

        # We need a currentContact set for isAttributeModifiable to work;
        # normally this is set by the app
        me = pim.Contact(itsView=view, displayName=u'me',
            references=[schema.ns('osaf.pim', view).currentContact]
        )

        # Add the subject to a read-only share:

        share_ro = sharing.Share(itsView=view, displayName=uw("share_ro"))
        share_ro.mode = 'get'

        e1.sharedIn.append(share_ro)

        # Test modifiability against...

        print e1.sharedIn

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
