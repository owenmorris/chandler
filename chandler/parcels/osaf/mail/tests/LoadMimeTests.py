__revision__  = "$Revision$"
__date__      = "$Date$"
__copyright__ = "Copyright (c) 2004 Open Source Applications Foundation"
__license__   = "http://osafoundation.org/Chandler_0.1_license_terms.htm"

import MailTestCase as MailTestCase
import osaf.mail.message as message
import osaf.contentmodel.mail.Mail as Mail
import email as email
import unittest as unittest
from repository.item.RefCollections import RefList
import application.Globals as Globals
import os

class LoadMimeTests(MailTestCase.MailTestCase):
    """Leverage the unit test api to load items in to the repository"""

    def testLoadMimeMessage(self):
        files = os.listdir("./mime_tests")
        files.sort()
        messageList = []


        for file in files:
            if not file.startswith('test_'):
                continue
            print "Loading: ", file
            messageObject = email.message_from_file(open("./mime_tests/%s" % file))
            mailMessage   = message.messageObjectToKind(messageObject)
            Globals.repository.view.commit()

    def setUp(self):
        super(LoadMimeTests, self).setUp()
        self.loadParcel("http://osafoundation.org/parcels/osaf/contentmodel/mail")

if __name__ == "__main__":
   unittest.main()
