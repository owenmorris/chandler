__revision__  = "$Revision$"
__date__      = "$Date$"
__copyright__ = "Copyright (c) 2004 Open Source Applications Foundation"
__license__   = "http://osafoundation.org/Chandler_0.1_license_terms.htm"

import osaf.framework.tasks.Action as Action
import application.Globals as Globals
import osaf.contentmodel.mail.Mail as Mail
import repository.item.Query as Query
import imap as imap
import smtp as smtp
import common as common
import message as message
import logging as logging
import twisted.internet.defer as defer


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
        accountKind = Mail.MailParcel.getSMTPAccountKind()
        account = None

        for acc in Query.KindQuery().run([accountKind]):
            account = acc
            break

        m = Mail.MailMessage()

        ea = Mail.EmailAddress()
        ea.emailAddress = "brian@localhost"
        ea.fullName = "Brian Kirsch"

        ea1 = Mail.EmailAddress()
        ea1.emailAddress = "bkirsch@osafoundation.org"
        ea1.fullName = "Brian Kirsch"

        ea2 = Mail.EmailAddress()
        ea2.emailAddress = "bkmuzic@yahoo.com"
        ea2.fullName = "Brian Kirsch"

        m.toAddress.append(ea)
        #m.toAddress.append(ea1)
        #m.ccAddress.append(ea2)

        m.fromAddress = ea1
        m.replyToAddress = ea
        m.subject = "This is a Test From SMTPSenderAction"
        m.body = message.strToText(m, "body", "This is some body Text")
        m.inReplyTo = "TEST"

        Globals.repository.commit()

        d = defer.Deferred().addBoth(self.smtpResponse)

        smtp.SMTPSender(account, m, d).sendMail()

    def smtpResponse(selfi, result):
        print "SMTP Response Got: ", result
