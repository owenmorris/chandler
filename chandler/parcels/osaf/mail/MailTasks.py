__revision__  = "$Revision$"
__date__      = "$Date$"
__copyright__ = "Copyright (c) 2004 Open Source Applications Foundation"
__license__   = "http://osafoundation.org/Chandler_0.1_license_terms.htm"

import osaf.framework.tasks.Action as Action
import debug as debug
import logging as logging


class IMAPDownloadAction(Action.Action):

    def Execute(self, task):
        """
        This method creates a C{IMAPDownloader} instance for each
        C{IMAPAccountKind} of type IMAP4 gotten via a:a

        accountKind = Mail.MailParcel.getIMAPAccountKind()

        @param task: The task object passed to the action
        @type task: C{osaf.framework.tasks.Task.Task}
        @return: C{None}
        """
        debug.downloadIMAPMail()


class SMTPSendAction(Action.Action):
    def Execute(self, task):
        debug.sendSMTPMessage()
