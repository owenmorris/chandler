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

"""
Unit tests for 
"""

import unittest, os

import osaf.pim.tests.TestDomainModel as TestDomainModel
import osaf.pim.mail as Mail
from osaf.pim import has_stamp, Modification, Note, ContentItem
from application import schema
from osaf.framework import password
from osaf.framework.twisted import waitForDeferred
from osaf.communicationstatus import CommunicationStatus
from osaf.sharing import SharedItem

from datetime import datetime
from chandlerdb.util.Path import Path
from i18n.tests import uw

class CommunicationStatusTestCase(TestDomainModel.DomainModelTestCase):
    def setUp(self):
        super(CommunicationStatusTestCase, self).setUp()
        self.address = Mail.EmailAddress(
                        itsView=self.view,
                        fullName=u"Mr. President",
                        emailAddress=u"kemal@aturk.tr")
        #account = Mail.IMAPAccount(itsView=self.view,
        #                           replyToAddress=self.address)
        schema.ns('osaf.pim', self.view).meEmailAddressCollection.add(self.address)
        self.note = Note(itsView=self.view)


    def testOrder(self):
        self.failUnless(CommunicationStatus.UPDATE      <
                        CommunicationStatus.OUT         <
                        CommunicationStatus.IN          <
                        CommunicationStatus.NEITHER     <
                        CommunicationStatus.EDITED      <
                        CommunicationStatus.SENT        <
                        CommunicationStatus.ERROR       <
                        CommunicationStatus.QUEUED      <
                        CommunicationStatus.DRAFT       <
                        CommunicationStatus.NEEDS_REPLY <
                        CommunicationStatus.READ)

    def checkStatus(self, startStatus, *flagNames):
        expectedStatus = startStatus
        for name in flagNames:
            expectedStatus |= getattr(CommunicationStatus, name)
        status = CommunicationStatus(self.note).status
        self.failUnlessEqual(status, expectedStatus, 
            "Unexpected communication status: got %s, expected %s" % 
            (CommunicationStatus.dump(status), 
             CommunicationStatus.dump(expectedStatus)))

    def testNote(self):
        self.checkStatus(0)
        self.note.changeEditState(Modification.edited)
        self.checkStatus(0) # edited has no effect till created
        self.note.changeEditState(Modification.created)
        self.checkStatus(0)
        self.note.changeEditState(Modification.edited)
        self.checkStatus(0, 'EDITED')
        
        si = SharedItem(self.note)
        si.add()
        si.generateConflicts()
        self.checkStatus(0, 'EDITED', 'ERROR')
        

    def testMail(self):
        self.note = Note(itsView=self.view)
        Mail.MailStamp(self.note).add()
        self.checkStatus(0, 'DRAFT', 'NEITHER')

        # Remove the MailStamp; that should make it no longer a Draft
        Mail.MailStamp(self.note).remove()
        self.checkStatus(0)


    def runMailTest(self, incoming=False, outgoing=False):

        self.note = Note(itsView=self.view)

        mail = Mail.MailStamp(self.note)
        mail.add()
        self.checkStatus(0, 'DRAFT', 'NEITHER')

        inoutFlags = 0
        if incoming:
            inoutFlags |= CommunicationStatus.IN
            mail.toAddress = self.address
        if outgoing:
            inoutFlags |= CommunicationStatus.OUT
            mail.fromAddress = self.address
        elif not incoming:
            inoutFlags |= CommunicationStatus.NEITHER

        self.checkStatus(inoutFlags, 'DRAFT')        

        self.note.changeEditState(Modification.queued)
        self.checkStatus(inoutFlags, 'QUEUED')        

        self.note.changeEditState(Modification.sent)
        self.checkStatus(inoutFlags, 'SENT')

        self.note.changeEditState(Modification.edited)
        self.checkStatus(inoutFlags, 'EDITED', 'UPDATE', 'DRAFT')

        # Remove the MailStamp; that should make it no longer a Draft
        mail.remove()
        self.checkStatus(0, 'EDITED')

        # Re-add the stamp
        mail.add()
        self.checkStatus(inoutFlags, 'EDITED', 'UPDATE', 'DRAFT')

        # and finally, re-send it
        self.note.changeEditState(Modification.updated)
        self.checkStatus(inoutFlags, 'UPDATE', 'SENT')


    def testOutgoingMail(self):
        self.runMailTest(outgoing=True)

    def testIncomingMail(self):
        self.runMailTest(incoming=True)

    def testInOutMail(self):
        self.runMailTest(incoming=True, outgoing=True)

if __name__ == "__main__":
    unittest.main()
