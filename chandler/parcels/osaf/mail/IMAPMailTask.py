__revision__  = "$Revision$"
__date__      = "$Date$"
__copyright__ = "Copyright (c) 2002 Open Source Applications Foundation"
__license__   = "http://osafoundation.org/Chandler_0.1_license_terms.htm"

import osaf.framework.tasks.Action as Action
import osaf.contentmodel.mail.Mail as Mail
import repository.item.Query as Query
import imap as imap


class MailDownloadAction(Action.Action):

    def Execute(self, task):
        """
        This method creates a C{IMAPDownloader} instance for each
        C{EmailAccountKind} of type IMAP4 gotten via a:a

        accountKind = Mail.MailParcel.getEmailAccountKind()

        @param task: The task object passed to the action
        @type task: C{osaf.framework.tasks.Task.Task}
        @return: C{None}
        """

        accountKind = Mail.MailParcel.getEmailAccountKind()
        printed = False

        for account in Query.KindQuery().run([accountKind]):
            if account.accountType != 'IMAP4':
                str =  "WARNING: Only IMAP Accounts are currently supported. "
                str1 = "%s of type %s will be ignored" % (account.displayName, account.accountType)
                logging.error(str, str1)
                continue

            if not printed:
                logging.info("IMAP MAIL TASK CHECKING FOR NEW MAIL")
                printed = True

            imap.IMAPDownloader(account).getMail()
