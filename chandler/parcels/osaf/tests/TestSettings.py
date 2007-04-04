#   Copyright (c) 2003-2007 Open Source Applications Foundation
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


import unittest, os, logging
from osaf import pim, sharing, settings
from osaf.framework import MasterPassword, password
from osaf.framework.twisted import waitForDeferred
from util import testcase
from application import schema
from chandlerdb.util.c import UUID


logger = logging.getLogger(__name__)


class SettingsTestCase(testcase.SingleRepositoryTestCase):

    def setUp(self):

        super(SettingsTestCase, self).setUp()

        from application.Utility import initPlugins
        initPlugins(None, ['plugins'])

    def runTest(self):
        self.setUp()
        self.dir = os.path.join(os.getenv("CHANDLERHOME") or ".",
            "parcels", "osaf", "tests")
        self.restoreSettings()

        prefs = schema.ns("osaf.framework.MasterPassword",
                  self.view).masterPasswordPrefs
        saved = os.path.join(self.dir, 'save.ini')
        
        settings.save(self.view, saved)
        
        try:
            self.restoreSettings(filename='save.ini')
            MasterPassword._change('', 'foo', self.view, prefs)
            settings.save(self.view, saved)
            self.restoreSettings(filename='save.ini', masterPassword='foo')
        finally:
            os.remove(saved)
            waitForDeferred(MasterPassword.clear())
            
    def restoreSettings(self, filename='settings.ini', masterPassword=''):

        rv = self.view

        # If we don't load osaf.app now, before restoring settings, it will
        # get loaded afterwards, which messes up the notion of "current"
        # accounts
        schema.ns("osaf.app", rv).me


        # restore settings
        settings.restore(rv, os.path.join(self.dir, filename),
                         testmode=True, newMaster=masterPassword)


        # verify accounts

        # Get the current Sharing account which should be
        # the "Test Sharing Service" account
        act = schema.ns("osaf.sharing", rv).currentSharingAccount.item
        self.assert_(act)
        self.assert_(isinstance(act, sharing.WebDAVAccount))
        self.assertEquals(act.displayName, "Test Sharing Service")
        self.assertEquals(act.port, 443)
        self.assertEquals(act.useSSL, True)
        self.assertEquals(act.host, "cosmo-demo.osafoundation.org")
        self.assertEquals(act.username, "sharing")
        self.assertEquals(waitForDeferred(act.password.decryptPassword(masterPassword=masterPassword)), "sharing_password")
        self.assertRaises(password.DecryptionError, waitForDeferred, act.password.decryptPassword(masterPassword=masterPassword+'A'))

        act = rv.findUUID(UUID("1bfc2a92-53eb-11db-9367-d2f16e571a03"))
        self.assert_(act)
        self.assertEquals(act.displayName, "Another Sharing Service")
        self.assertEquals(act.port, 8080)
        self.assertEquals(act.useSSL, False)

        act = rv.findUUID(UUID("1bfd96f2-53eb-11db-9367-d2f16e571a02"))
        self.assert_(act)
        self.assert_(isinstance(act, pim.mail.SMTPAccount))
        self.assertEquals(act.displayName, "Test Outgoing SMTP mail")
        self.assertEquals(act.host, "smtp.example.com")
        self.assertEquals(act.useAuth, True)
        self.assertEquals(act.username, "smtp")
        self.assertEquals(waitForDeferred(act.password.decryptPassword(masterPassword=masterPassword)), "smtp_password")
        self.assertEquals(act.port, 465)
        self.assertEquals(act.connectionSecurity, "SSL")

        act = rv.findUUID(UUID("1bffa488-53eb-11db-9367-d2f16e571a02"))
        self.assert_(act)
        self.assert_(isinstance(act, pim.mail.IMAPAccount))
        self.assertEquals(act.host, "imap.example.com")
        self.assertEquals(act.username, "imap")
        self.assertEquals(waitForDeferred(act.password.decryptPassword(masterPassword=masterPassword)), "imap_password")
        self.assertEquals(act.port, 993)
        self.assertEquals(act.connectionSecurity, "SSL")

        # Get the current Mail account which should be
        # the pop.example.com account
        act = schema.ns("osaf.pim", rv).currentIncomingAccount.item
        self.assert_(act)
        self.assert_(isinstance(act, pim.mail.POPAccount))
        self.assertEquals(act.host, "pop.example.com")
        self.assertEquals(act.username, "pop")
        self.assertEquals(waitForDeferred(act.password.decryptPassword(masterPassword=masterPassword)), "pop_password")
        self.assertEquals(act.port, 995)
        self.assertEquals(act.connectionSecurity, "SSL")


        # verify shares

        mine = schema.ns("osaf.pim", rv).mine

        foundA = False
        foundB = False
        for col in pim.ContentCollection.iterItems(rv):
            name = getattr(col, "displayName", "")
            if name == "pub_mine":
                foundA = True
                self.assert_(col in mine.sources)

            elif name == "sub_notmine":
                foundB = True
                self.assert_(col not in mine.sources)

        self.assert_(foundA and foundB)


        # verify timezone
        self.assert_(schema.ns("osaf.pim", rv).TimezonePrefs.showUI)

        # verify visible hours
        calPrefs = schema.ns("osaf.framework.blocks.calendar", rv).calendarPrefs
        self.assertEquals(calPrefs.visibleHours, 24)
        self.assertEquals(calPrefs.hourHeightMode, "visibleHours")


if __name__ == "__main__":
    unittest.main()
