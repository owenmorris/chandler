__revision__  = "$Revision$"
__date__      = "$Date$"
__copyright__ = "Copyright (c) 2004 Open Source Applications Foundation"
__license__   = "http://osafoundation.org/Chandler_0.1_license_terms.htm"

import osaf.framework.tasks.Action as Action
import osaf.contentmodel.mail.Mail as Mail
import repository.item.Query as Query
import imap as imap
import smtp as smtp
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

        accountKind = Mail.MailParcel.getIMAPAccountKind()
        printed = False

        for account in Query.KindQuery().run([accountKind]):

            if not printed:
                logging.info("IMAP MAIL TASK CHECKING FOR NEW MAIL")
                printed = True

            imap.IMAPDownloader(account).getMail()


class SMTPSendAction(Action.Action):
    def Execute(self, task):

       logging.info("SENDING STMP MAIL")
       #smtp.SMTPSender().sendmail()
