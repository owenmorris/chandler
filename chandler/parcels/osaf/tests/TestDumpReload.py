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


from application import schema
import unittest, sys, os, logging
from osaf import pim, dumpreload, sharing
from osaf.pim import mail
from osaf.framework.password import Password
from osaf.framework.twisted import waitForDeferred
from util import testcase
from PyICU import ICUtzinfo
import datetime

logger = logging.getLogger(__name__)


class DumpReloadTestCase(testcase.DualRepositoryTestCase):

    def runTest(self):
        self.setUp()
        self.RoundTrip()

    def RoundTrip(self):

        filename = "tmp_dump_file"

        view0 = self.views[0]
        view1 = self.views[1]

        # uuids to dump; add your items to this:
        uuids = set()

        # Prepare test data

        coll0 = pim.SmartCollection("testCollection", itsView=view0,
            displayName="Test Collection")
        uuids.add(coll0.itsUUID)

        titles = [
            u"dunder",
            u"mifflin",
        ]

        tzinfo = ICUtzinfo.floating
        createdOn = datetime.datetime(2007, 3, 1, 10, 0, 0, 0, tzinfo)
        lastModified = datetime.datetime(2007, 3, 1, 12, 0, 0, 0, tzinfo)
        email = "test@example.com"
        emailAddress = pim.EmailAddress.getEmailAddress(view0, email)

        count = len(titles)
        for i in xrange(count):
            n = pim.Note(itsView=view0)
            n.createdOn = createdOn
            n.displayName = titles[i % count]
            n.body = u"Here is the body"
            n.lastModifiedBy = emailAddress
            n.lastModified = lastModified
            coll0.add(n)
            uuids.add(n.itsUUID)


        # Sharing related items
        account0 = sharing.CosmoAccount(itsView=view0,
            host="chandler.o11n.org",
            port=1888,
            path="/cosmo",
            username="test",
            password=Password(itsView=view0),
            userSSL=True
        )
        uuids.add(account0.itsUUID)
        cosmo_conduit0 = sharing.CosmoConduit(itsView=view0,
            account=account0,
            shareName=coll0.itsUUID.str16(),
            translator=sharing.SharingTranslator,
            serializer=sharing.EIMMLSerializer
        )
        uuids.add(cosmo_conduit0.itsUUID)
        cosmo_share0 = sharing.Share(itsView=view0,
            contents=coll0,
            conduit=cosmo_conduit0
        )
        uuids.add(cosmo_share0.itsUUID)


        inmemory_conduit0 = sharing.InMemoryDiffRecordSetConduit(itsView=view0,
            shareName="in_memory",
            translator=sharing.SharingTranslator,
            serializer=sharing.EIMMLSerializer
        )
        uuids.add(inmemory_conduit0.itsUUID)

        inmemory_share0 = sharing.Share(itsView=view0,
            conduit=inmemory_conduit0,
            contents=coll0
        )
        uuids.add(inmemory_share0.itsUUID)

        # Create some State objects
        inmemory_share0.create()
        view0.commit()
        inmemory_share0.sync()
        for state in inmemory_share0.states:
            uuids.add(state.itsUUID)

        # passwords
        pw = Password(itsView=view0)
        waitForDeferred(pw.encryptPassword('foobar'))
        uuids.add(pw.itsUUID)
        # XXX password prefs
        # XXX passwords as part of accounts

        #Mail Accounts

        imapAddress = mail.EmailAddress(itsView=view0,
                                       fullName = "test",
                                       emailAddress = "test@test.com")

        popAddress = mail.EmailAddress(itsView=view0,
                                       fullName = "test1",
                                       emailAddress = "test1@test.com")

        smtpOldAddress = mail.EmailAddress(itsView=view0,
                                       fullName = "test2",
                                       emailAddress = "test2@test.com")

        smtpNewAddress = mail.EmailAddress(itsView=view0,
                                       fullName = "test3",
                                       emailAddress = "test3@test.com")


        testFolder = mail.IMAPFolder(itsView=view0,
                                    displayName = "TestFolder",
                                    folderName = "INBOX.TestFolder",
                                    folderType = "MAIL")

        queuedMessage0 = pim.MailStamp(pim.Note(itsView=view0))
        queuedMessage0.add()

        queuedMessage0.subject = "Test for SMTP Queue"

        uuids.add(queuedMessage0.itsItem.itsUUID)

        imapaccount0 = mail.IMAPAccount(itsView=view0,
            displayName = "IMAP Test",
            host="localhost",
            port=143,
            username="test",
            password=Password(itsView=view0),
            connectionSecurity = "TLS",
            numRetries = 2,
            pollingFrequency = 300,
            timeout = 50,
            isActive = False,
            replyToAddress = imapAddress,
            folders = [testFolder],
        )


        uuids.add(imapaccount0.itsUUID)

        popaccount0 = mail.POPAccount(itsView=view0,
            displayName = "POP Test",
            host="localhost",
            port=110,
            username="test1",
            password=Password(itsView=view0),
            connectionSecurity = "NONE",
            numRetries = 3,
            pollingFrequency = 200,
            timeout = 40,
            isActive = True,
            replyToAddress = popAddress,
        )

        uuids.add(popaccount0.itsUUID)

        smtpaccount0 = mail.SMTPAccount(itsView=view0,
            displayName = "SMTP Test",
            host="localhost",
            port=587,
            username="test2",
            password=Password(itsView=view0),
            connectionSecurity = "SSL",
            numRetries = 5,
            pollingFrequency = 500,
            timeout = 60,
            isActive = True,
            fromAddress = smtpOldAddress,
            useAuth = True,
            messageQueue = [queuedMessage0.itsItem],
        )

        # This orphans smtpOldAddress leaving it as
        # an old me address which is stored in the
        # meEmailAddressCollection.
        # The purpose of this is to test dump and reload
        # of the meEmailAddressCollection.
        smtpaccount0.fromAddress = smtpNewAddress

        uuids.add(smtpaccount0.itsUUID)

        #Take the mail service offline
        schema.ns("osaf.pim", view0).MailPrefs.isOnline = False

        # Calendar prefs
        pref = schema.ns('osaf.pim', view0).TimezonePrefs
        pref.showUI = True # change from default
        pref.showPrompt = False # change from default

        pref = schema.ns('osaf.framework.blocks.calendar', view0).calendarPrefs
        pref.hourHeightMode = "auto"
        pref.visibleHours = 20

        # TODO: TimeZoneInfo

        try:

            dumpreload.dump(view0, filename)
            dumpreload.reload(view1, filename)

            # Ensure the items are now in view1
            for uuid in uuids:
                item0 = view0.findUUID(uuid)
                item1 = view1.findUUID(uuid)

                self.assert_(item1 is not None)
                if hasattr(item0, 'displayName'):
                    self.assertEqual(item0.displayName, item1.displayName)
                if hasattr(item0, 'body'):
                    self.assertEqual(item0.body, item1.body)

            # Verify collection membership:
            coll1 = view1.findUUID(coll0.itsUUID)
            for item0 in coll0:
                item1 = view1.findUUID(item0.itsUUID)
                self.assert_(item1 in coll1)


            # Verify sharing
            inmemory_share1 = view1.findUUID(inmemory_share0.itsUUID)
            self.assert_(inmemory_share1 is not None)
            self.assertEqual(inmemory_share0.contents.itsUUID,
                inmemory_share1.contents.itsUUID)
            self.assertEqual(inmemory_share0.conduit.syncToken,
                inmemory_share1.conduit.syncToken)
            for state0 in inmemory_share0.states:
                state1 = view1.findUUID(state0.itsUUID)
                self.assert_(state1 in inmemory_share1.states)
                self.assertEqual(state0.agreed, state1.agreed)
                self.assertEqual(state0.pending, state1.pending)
            for item0 in coll0:
                item1 = view1.findUUID(item0.itsUUID)
                sharedItem1 = sharing.SharedItem(item1)
                self.assert_(inmemory_share1 in sharedItem1.sharedIn)


            # Verify Calendar prefs
            pref = schema.ns('osaf.pim', view1).TimezonePrefs
            self.assertEqual(pref.showUI, True)
            self.assertEqual(pref.showPrompt, False)

            pref = schema.ns('osaf.framework.blocks.calendar',
                view1).calendarPrefs
            self.assertEqual(pref.hourHeightMode, "auto")
            self.assertEqual(pref.visibleHours, 20)

            # Verify passwords
            pw1 = view1.findUUID(pw.itsUUID)
            self.assertEqual(waitForDeferred(pw.decryptPassword()),
                             waitForDeferred(pw1.decryptPassword()))

            #Verify Mail Accounts

            imapaccount1 = view1.findUUID(imapaccount0.itsUUID)
            self.assertEquals(imapaccount1.host, "localhost")
            self.assertEquals(imapaccount1.port, 143)
            self.assertEquals(imapaccount1.username, "test")
            self.assertEquals(imapaccount1.connectionSecurity, "TLS")
            self.assertEquals(imapaccount1.numRetries, 2)
            self.assertEquals(imapaccount1.pollingFrequency, 300)
            self.assertEquals(imapaccount1.timeout, 50)
            self.assertEquals(imapaccount1.isActive, False)
            self.assertEquals(imapaccount1.replyToAddress.format(), imapAddress.format())

            folder = imapaccount1.folders.first()
            self.assertEquals(folder.displayName, "TestFolder")
            self.assertEquals(folder.folderName, "INBOX.TestFolder")
            self.assertEquals(folder.folderType, "MAIL")

            popaccount1 = view1.findUUID(popaccount0.itsUUID)

            self.assertEquals(popaccount1.host, "localhost")
            self.assertEquals(popaccount1.port, 110)
            self.assertEquals(popaccount1.username, "test1")
            self.assertEquals(popaccount1.connectionSecurity, "NONE")
            self.assertEquals(popaccount1.numRetries, 3)
            self.assertEquals(popaccount1.pollingFrequency, 200)
            self.assertEquals(popaccount1.timeout, 40)
            self.assertEquals(popaccount1.isActive, True)
            self.assertEquals(popaccount1.replyToAddress.format(), popAddress.format())

            smtpaccount1 = view1.findUUID(smtpaccount0.itsUUID)

            self.assertEquals(smtpaccount1.host, "localhost")
            self.assertEquals(smtpaccount1.port, 587)
            self.assertEquals(smtpaccount1.username, "test2")
            self.assertEquals(smtpaccount1.connectionSecurity, "SSL")
            self.assertEquals(smtpaccount1.numRetries, 5)
            self.assertEquals(smtpaccount1.pollingFrequency, 500)
            self.assertEquals(smtpaccount1.timeout, 60)
            self.assertEquals(smtpaccount1.isActive, True)
            self.assertEquals(smtpaccount1.useAuth, True)
            self.assertEquals(smtpaccount1.fromAddress.format(), smtpNewAddress.format())

            queuedMessage1 = smtpaccount1.messageQueue[0]

            self.assertEquals(queuedMessage1.itsUUID, queuedMessage0.itsItem.itsUUID)
            self.assertEquals(schema.ns("osaf.pim", view1).MailPrefs.isOnline, False)

            col = schema.ns("osaf.pim", view1).meEmailAddressCollection

            found = False
            oldAddr = smtpOldAddress.format()

            # Confirm that the old email address smtpOldAddress
            # is in the meEmailAddressCollection for calculating
            # the MailStamp.fromMe and MailStamp.toMe attributes
            for ea in col:
                if ea.format() == oldAddr:
                    found = True
                    break

            self.assertTrue(found)
            
        finally:
            os.remove(filename)


if __name__ == "__main__":
    unittest.main()
