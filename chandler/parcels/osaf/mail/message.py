__revision__  = "$Revision$"
__date__      = "$Date$"
__copyright__ = "Copyright (c) 2004 Open Source Applications Foundation"
__license__   = "http://osafoundation.org/Chandler_0.1_license_terms.htm"

import osaf.contentmodel.mail.Mail as Mail
import mx.DateTime as DateTime
import email as email
import email.Message as Message
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

def messageTextToKind(messageText):
    """
    This method converts a email message string to
    a Chandler C{Mail.MailMessage} object

    @param messageText: A string representation of a mail message
    @type messageText: string
    @return: C{Mail.MailMessage}
    """

    if not isinstance(messageText, str):
        raise TypeError("messageText must be a String")

    return messageObjectToKind(email.message_from_string(messageText))

def messageObjectToKind(messageObject):
    """
    This method converts a email message string to
    a Chandler C{Mail.MailMessage} object

    @param messageObject: A C{email.Message} object representation of a mail message
    @type messageObject: C{email.Message}
    @return: C{Mail.MailMessage}
    """

    if not isinstance(messageObject, Message.Message):
        raise TypeError("messageObject must be a Python email.Message.Message instance")

    m = Mail.MailMessage()

    if m is None:
        raise Exception("Repository returned a MailMessage that was None")

    m.dateSent = DateTime.mktime(Utils.parsedate(messageObject['Date']))
    m.dateReceived = DateTime.now()

    if messageObject['Subject'] is None:
        m.subject = ""
    else:
        m.subject = messageObject['Subject']

    # XXX replyAddress should really be the Reply-to header, not From
    m.replyAddress = Mail.EmailAddress()
    m.replyAddress.emailAddress = format_addr(Utils.parseaddr(messageObject['From']))

    m.toAddress = []
    for addr in Utils.getaddresses(messageObject.get_all('To', [])):
        ea = Mail.EmailAddress()
        ea.emailAddress = format_addr(addr)
        m.toAddress.append(ea)

    m.ccAddress = []
    for addr in Utils.getaddresses(messageObject.get_all('Cc', [])):
        ea = Mail.EmailAddress()
        ea.emailAddress = format_addr(addr)
        m.ccAddress.append(ea)

    return m

def KindToMessageObject(mailMessage):
    """
    This method converts a email message string to
    a Chandler C{Mail.MailMessage} object

    @param messageObject: A C{email.Message} object representation of a mail message
    @type messageObject: C{email.Message}
    @return: C{Mail.MailMessage}
    """

    ### Check that the kind is a mail message
    if not isinstance(mailMessage, Mail.MailMessage):
        raise Exception("mailMessage must be an instance of Kind Mail.MailMessage")


    messageObject = Message.Message()

    return messageObject
