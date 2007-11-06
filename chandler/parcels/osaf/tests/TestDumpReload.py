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


from application import schema
import unittest, os, os.path, logging
from osaf import pim, dumpreload, sharing
from osaf.pim import mail
from osaf.framework.password import Password
from osaf.framework import MasterPassword
from osaf.framework.twisted import waitForDeferred
from util import testcase
import datetime
 
logger = logging.getLogger(__name__)


class DumpReloadTestCase(testcase.DualRepositoryTestCase):

    def runTest(self):
        self.setUp()
        try:
            self.RoundTrip()
            self.BackwardsCompatibility()
        finally:
            # otherwise test hangs waiting for Timer thread to finish
            waitForDeferred(MasterPassword.clear())

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

        tzinfo = view0.tzinfo.floating
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


        # Read/unread items
        readNote = pim.Note(itsView=view0, read=True)
        unreadNote = pim.Note(itsView=view0, read=False)


        # "Private" items
        publicNote = pim.Note(itsView=view0, private=False)
        privateNote = pim.Note(itsView=view0, private=True)


        # Mine/Not-Mine/Dashboard

        directlyInDashboard = pim.Note(itsView=view0)
        dashboard = schema.ns("osaf.pim", view0).allCollection
        dashboard.add(directlyInDashboard)

        aMineCollection = pim.SmartCollection(itsView=view0)
        schema.ns('osaf.pim', view0).mine.addSource(aMineCollection)
        inMine = pim.Note(itsView=view0)
        aMineCollection.add(inMine)

        aNotMineCollection = pim.SmartCollection(itsView=view0)
        inNotMine = pim.Note(itsView=view0)
        aNotMineCollection.add(inNotMine)


        trash = schema.ns("osaf.pim", view0).trashCollection
        trashTestCollection = pim.SmartCollection(itsView=view0)
        trashedItem = pim.Note(itsView=view0)
        trashTestCollection.add(trashedItem)
        trash.add(trashedItem)
        self.assert_(trashedItem in trashTestCollection.inclusions)
        self.assert_(trashedItem not in trashTestCollection)
        self.assert_(trashedItem in trash)

        # Sharing related items
        account0 = sharing.CosmoAccount(itsView=view0,
            host="chandler.o11n.org",
            port=8080,
            path="/cosmo",
            username="test",
            password=Password(itsView=view0),
            useSSL=True
        )
        waitForDeferred(account0.password.encryptPassword('4cc0unt0'))
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


        hub_account0 = sharing.HubAccount(itsView=view0,
            username="test",
            password=Password(itsView=view0),
        )
        waitForDeferred(hub_account0.password.encryptPassword('4cc0unt0'))
        uuids.add(hub_account0.itsUUID)


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
        # Set one of the states to be a pendingRemoval
        pendingRemoval = state.itsUUID
        state.pendingRemoval = True


        # Peer states
        peerNote = pim.Note(itsView=view0)
        peerAddress = pim.EmailAddress(itsView=view0,
            fullName="Michael Scott",
            emailAddress="greatscott@dundermifflin.com")
        peerState = sharing.State(itsView=view0,
            conflictFor=peerNote,
            peer=peerAddress,
        )
        sharing.SharedItem(peerNote).add()
        sharedPeerNote = sharing.SharedItem(peerNote)
        sharedPeerNote.peerStates = []
        sharedPeerNote.peerStates.append(peerState, peerAddress.itsUUID.str16())
        uuids.add(peerNote.itsUUID)
        uuids.add(peerAddress.itsUUID)
        uuids.add(peerState.itsUUID)

        # Sharing proxy
        proxy = sharing.getProxy(view0)
        proxy.host = "host"
        proxy.port = 123
        proxy.username = "username"
        proxy.passwd = "password"
        proxy.active = True
        proxy.useAuth = True
        proxy.bypass = "192.168.1, localhost"
        uuids.add(proxy.itsUUID)

        # Online state
        schema.ns('osaf.app', view0).prefs.isOnline = False
        schema.ns('osaf.sharing', view0).prefs.isOnline = False

        #Mail Accounts

        imapAddress = mail.EmailAddress.getEmailAddress(view0, "test@test.com", 
                                                        "test")

        popAddress = mail.EmailAddress.getEmailAddress(view0, "test1@test.com", 
                                                       "test1")

        smtpOldAddress = mail.EmailAddress.getEmailAddress(view0, 
                                                           "test2@test.com", 
                                                           "test2")

        smtpNewAddress = mail.EmailAddress.getEmailAddress(view0, 
                                                           "test3@test.com", 
                                                           "test3")


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
            isActive = False,
            replyToAddress = imapAddress,
            folders = [testFolder],
        )
        waitForDeferred(imapaccount0.password.encryptPassword('imap4acc0unt0'))

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
            isActive = True,
            replyToAddress = popAddress,
        )
        waitForDeferred(popaccount0.password.encryptPassword('pop4acc0unt0'))

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
            isActive = True,
            fromAddress = smtpOldAddress,
            useAuth = True,
            messageQueue = [queuedMessage0.itsItem],
        )
        waitForDeferred(smtpaccount0.password.encryptPassword('smtp4acc0unt0'))

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

        # passwords
        pw = Password(itsView=view0)
        waitForDeferred(pw.encryptPassword('foobar'))
        uuids.add(pw.itsUUID)
        # password prefs
        mpwPrefs = schema.ns("osaf.framework.MasterPassword",
                             view0).masterPasswordPrefs
        MasterPassword._change('', 'secret', view0, mpwPrefs)
        mpwPrefs.timeout = 10



        # Ensure sidebar is loaded in view1
        sidebar1 = schema.ns("osaf.app", view1).sidebarCollection

        try:

            dumpreload.dump(view0, filename)
            dumpreload.reload(view1, filename, testmode=True)

            # Ensure the items are now in view1
            for uuid in uuids:
                item0 = view0.findUUID(uuid)
                item1 = view1.findUUID(uuid)

                self.assert_(item1 is not None)
                if hasattr(item0, 'displayName'):
                    self.assertEqual(item0.displayName, item1.displayName)
                if hasattr(item0, 'body'):
                    self.assertEqual(item0.body, item1.body)

            # Verify ContentItem.read
            self.assert_(view1.findUUID(readNote.itsUUID).read is True)
            self.assert_(view1.findUUID(unreadNote.itsUUID).read is False)

            # Verify ContentItem.private
            self.assert_(view1.findUUID(publicNote.itsUUID).private is False)
            self.assert_(view1.findUUID(privateNote.itsUUID).private is True)


            # Verify Mine/Not-Mine/Dashboard
            dashboard = schema.ns("osaf.pim", view1).allCollection
            self.assert_(view1.findUUID(directlyInDashboard.itsUUID) in
                dashboard.inclusions)

            self.assert_(view1.findUUID(inMine.itsUUID) in dashboard)
            self.assert_(view1.findUUID(inNotMine.itsUUID) not in dashboard)


            # Verify collection membership:
            coll1 = view1.findUUID(coll0.itsUUID)
            for item0 in coll0:
                item1 = view1.findUUID(item0.itsUUID)
                self.assert_(item1 in coll1)


            # Verify trash membership
            trash = schema.ns("osaf.pim", view1).trashCollection
            trashedItem = view1.findUUID(trashedItem.itsUUID)
            self.assert_(trashedItem in trash)
            trashTestCollection = view1.findUUID(trashTestCollection.itsUUID)
            self.assert_(trashedItem not in trashTestCollection)
            self.assert_(trashedItem in trashTestCollection.inclusions)



            # Verify passwords
            pw1 = view1.findUUID(pw.itsUUID)
            self.assertEqual(waitForDeferred(pw1.decryptPassword('secret')),
                             'foobar')
            
            mpwPrefs1 = schema.ns("osaf.framework.MasterPassword",
                                  view1).masterPasswordPrefs
            self.assertEqual(mpwPrefs1.masterPassword, True)
            self.assertEqual(mpwPrefs1.timeout, 10)
            
            pwPrefs1 = schema.ns("osaf.framework.password",
                                 view1).passwordPrefs
            self.assertEqual(len(waitForDeferred(pwPrefs1.dummyPassword.decryptPassword('secret'))), 16)
            self.assertEqual(str(pwPrefs1.dummyPassword.itsUUID),
                             'dd555441-9ddc-416c-b55a-77b073c7bd15')
            dummyByUUID = view1.findUUID('dd555441-9ddc-416c-b55a-77b073c7bd15')
            self.assertEqual(dummyByUUID, pwPrefs1.dummyPassword)
            
            count = 0
            for item in Password.iterItems(view0):
                waitForDeferred(item.decryptPassword('secret'))
                count += 1

            count1 = 0
            for item in Password.iterItems(view1):
                waitForDeferred(item.decryptPassword('secret'))
                count1 += 1
            
            self.assertEqual(count+2, count1) # XXX Shouldn't count==count1?
                
            # Verify sharing
            account1 = view1.findUUID(account0.itsUUID)
            self.assertEquals(account1.host, "chandler.o11n.org")
            self.assertEquals(account1.port, 8080)
            self.assertEquals(account1.path, "/cosmo")
            self.assertEquals(account1.username, "test")
            self.assertEquals(account1.useSSL, True)
            self.assertEquals(waitForDeferred(account1.password.decryptPassword('secret')),
                              '4cc0unt0')

            hub_account1 = view1.findUUID(hub_account0.itsUUID)
            self.assert_(isinstance(hub_account0, sharing.HubAccount))

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
                self.assertEqual(state1.pendingRemoval,
                    state1.itsUUID == pendingRemoval)
            for item0 in coll0:
                item1 = view1.findUUID(item0.itsUUID)
                sharedItem1 = sharing.SharedItem(item1)
                self.assert_(inmemory_share1 in sharedItem1.sharedIn)

            # Peer states
            peerNote1 = view1.findUUID(peerNote.itsUUID)
            sharedPeerNote1 = sharing.SharedItem(peerNote1)
            peerAddress1 = view1.findUUID(peerAddress.itsUUID)
            peerState1 = view1.findUUID(peerState.itsUUID)
            self.assert_(peerState1 in sharedPeerNote1.peerStates)
            self.assertEquals(sharedPeerNote1.peerStates.getAlias(peerState1),
                peerAddress1.itsUUID.str16())
            self.assert_(peerState1 in sharedPeerNote1.conflictingStates)
            self.assert_(isinstance(peerAddress1, pim.EmailAddress))


            proxy1 = view1.findUUID(proxy.itsUUID)
            self.assertEquals(proxy1.host, "host")
            self.assertEquals(proxy1.port, 123)
            self.assertEquals(proxy1.username, "username")
            self.assertEquals(proxy1.bypass, "192.168.1, localhost")

            pw = waitForDeferred(proxy1.password.decryptPassword('secret'))
            self.assertEquals(pw, "password")
            self.assertEquals(proxy1.active, True)
            self.assertEquals(proxy1.useAuth, True)

            self.assertEquals(schema.ns('osaf.app', view1).prefs.isOnline,
                False)
            self.assertEquals(schema.ns('osaf.sharing', view1).prefs.isOnline,
                False)

            # Verify Calendar prefs
            pref = schema.ns('osaf.pim', view1).TimezonePrefs
            self.assertEqual(pref.showUI, True)
            self.assertEqual(pref.showPrompt, False)

            pref = schema.ns('osaf.framework.blocks.calendar',
                view1).calendarPrefs
            self.assertEqual(pref.hourHeightMode, "auto")
            self.assertEqual(pref.visibleHours, 20)

            #Verify Mail Accounts

            imapaccount1 = view1.findUUID(imapaccount0.itsUUID)
            self.assertEquals(imapaccount1.host, "localhost")
            self.assertEquals(imapaccount1.port, 143)
            self.assertEquals(imapaccount1.username, "test")
            self.assertEquals(imapaccount1.connectionSecurity, "TLS")
            self.assertEquals(imapaccount1.numRetries, 2)
            self.assertEquals(imapaccount1.pollingFrequency, 300)
            self.assertEquals(imapaccount1.isActive, False)
            self.assertEquals(imapaccount1.replyToAddress.format(), imapAddress.format())
            self.assertEquals(waitForDeferred(imapaccount1.password.decryptPassword('secret')),
                              'imap4acc0unt0')

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
            self.assertEquals(popaccount1.isActive, True)
            self.assertEquals(popaccount1.replyToAddress.format(), popAddress.format())
            self.assertEquals(waitForDeferred(popaccount1.password.decryptPassword('secret')),
                              'pop4acc0unt0')

            smtpaccount1 = view1.findUUID(smtpaccount0.itsUUID)

            self.assertEquals(smtpaccount1.host, "localhost")
            self.assertEquals(smtpaccount1.port, 587)
            self.assertEquals(smtpaccount1.username, "test2")
            self.assertEquals(smtpaccount1.connectionSecurity, "SSL")
            self.assertEquals(smtpaccount1.numRetries, 5)
            self.assertEquals(smtpaccount1.pollingFrequency, 500)
            self.assertEquals(smtpaccount1.isActive, True)
            self.assertEquals(smtpaccount1.useAuth, True)
            self.assertEquals(smtpaccount1.fromAddress.format(), smtpNewAddress.format())
            self.assertEquals(waitForDeferred(smtpaccount1.password.decryptPassword('secret')),
                              'smtp4acc0unt0')

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





    def BackwardsCompatibility(self):
        path = os.path.join(os.getenv('CHANDLERHOME') or '.',
            'parcels', 'osaf', 'tests', 'compatibility.chex')
        view = self.views[0]
        dumpreload.reload(view, path, testmode=True)
        # check a loaded item
        coll = view.findUUID("2810afaa-1f7f-11dc-cefe-ad81e1bece23")
        self.assertTrue(isinstance(coll, pim.SmartCollection))



if __name__ == "__main__":
    unittest.main()
