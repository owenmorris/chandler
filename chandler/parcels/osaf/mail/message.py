__revision__  = "$Revision$"
__date__      = "$Date$"
__copyright__ = "Copyright (c) 2002 Open Source Applications Foundation"
__license__   = "http://osafoundation.org/Chandler_0.1_license_terms.htm"

import osaf.contentmodel.mail.Mail as Mail
import mx.DateTime as DateTime
import email as email
import email.Utils as Utils

def format_addr(addr):
    """
    This method formats an email address

    @param addr: The email address to format
    @type addr: list
    @return: C{string}
    """

    str = addr[0]
    if str != '':
        str = str + ' '
    str = str + '<' + addr[1] + '>'
    return str


def make_message(data):
    """
    This method converts a email message string to
    a Chandler C{Mail.MailMessage} object

    @param data: A string representation of a mail message
    @type data: string
    @return: C{Mail.MailMessage}
    """

    msg = email.message_from_string(data)

    m = Mail.MailMessage()

    if m is None:
        print "MailMessage was NULL"
        return None

    m.dateSent = DateTime.mktime(Utils.parsedate(msg['Date']))
    m.dateReceived = DateTime.now()

    if msg['Subject'] is None:
        m.subject = ""
    else:
        m.subject = msg['Subject']

    # XXX replyAddress should really be the Reply-to header, not From
    m.replyAddress = Mail.EmailAddress()
    m.replyAddress.emailAddress = format_addr(Utils.parseaddr(msg['From']))

    m.toAddress = []
    for addr in Utils.getaddresses(msg.get_all('To', [])):
        ea = Mail.EmailAddress()
        ea.emailAddress = format_addr(addr)
        m.toAddress.append(ea)

    m.ccAddress = []
    for addr in Utils.getaddresses(msg.get_all('Cc', [])):
        ea = Mail.EmailAddress()
        ea.emailAddress = format_addr(addr)
        m.ccAddress.append(ea)

    return m
