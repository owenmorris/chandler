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
    sharing.SMTPInvitationSender("http://test.com", ['brian@localhost', 'bkirsch@osafoundation.org']).sendInvitation()

def sendSMTPMessage():
    accountKind = Mail.MailParcel.getSMTPAccountKind()
    account = None

    for acc in Query.KindQuery().run([accountKind]):
        account = acc
        break

    m = Mail.MailMessage()

    ea = Mail.EmailAddress()
    ea.emailAddress = "brian@saofoundation.org"
    ea.fullName = "Brian Kirsch"

    ea1 = Mail.EmailAddress()
    ea1.emailAddress = "bkirsch@osafoundation.org"
    #ea1.fullName = "Brian Kirsch"

    ea2 = Mail.EmailAddress()
    ea2.emailAddress = "bbi.com"
    #ea2.fullName = "Brian Kirsch"

    ea3 = Mail.EmailAddress()
    ea3.emailAddress = "bill@test.com"

    ea4 = Mail.EmailAddress()
    ea4.emailAddress = "brian@yahoo.com"
    #ea.fullName = "Brian Kirsch"

    m.toAddress.append(ea1)
    #m.toAddress.append(ea2)
    #m.toAddress.append(ea3)
    #m.toAddress.append(ea4)
    # m.toAddress.append(ea1)
    #m.ccAddress.append(ea2)
    #m.bccAddress.append(ea)

    m.fromAddress = ea
    #m.replyToAddress = ea
    m.subject = "This is a Test From SMTPSenderAction"
    m.body = message.strToText(m, "body", "This is some body Text")

    Globals.repository.commit()

    smtp.SMTPSender(account, m).sendMail()
