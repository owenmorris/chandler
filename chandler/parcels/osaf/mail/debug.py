__revision__  = "$Revision$"
__date__      = "$Date$"
__copyright__ = "Copyright (c) 2004 Open Source Applications Foundation"
__license__   = "http://osafoundation.org/Chandler_0.1_license_terms.htm"

import application.Globals as Globals
import osaf.contentmodel.mail.Mail as Mail
import repository.item.Query as Query
import imap as imap
import smtp as smtp
import sharing as sharing
import common as common
import message as message
import logging as logging

def downloadIMAPMail():
    accountKind = Mail.MailParcel.getIMAPAccountKind()

    for account in Query.KindQuery().run([accountKind]):
        imap.IMAPDownloader(account).getMail()


def sendInvitation():
    sharing.sendInvitation("http://test.com", "In", ['brian@localhost'])

def sendSMTPMessage():
    account, replyToAddress = smtp.getSMTPAccount()

    m = Mail.MailMessage()

    ea = Mail.EmailAddress()
    ea.emailAddress = "brian@localhost"
    ea.fullName = "Brian Kirsch"

    ea1 = Mail.EmailAddress()
    ea1.emailAddress = "brian@localhost"
    ea1.fullName = "Brian Kirsch"


    m.toAddress.append(ea)
    #m.toAddress.append(ea1)

    m.fromAddress = replyToAddress
    m.subject = "This is a Test From SMTPSenderAction"
    m.body = message.strToText(m, "body", "This is some body Text")

    Globals.repository.commit()

    smtp.SMTPSender(account, m).sendMail()
