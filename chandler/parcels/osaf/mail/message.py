__revision__  = "$Revision$"
__date__      = "$Date$"
__copyright__ = "Copyright (c) 2004 Open Source Applications Foundation"
__license__   = "http://osafoundation.org/Chandler_0.1_license_terms.htm"

import osaf.contentmodel.mail.Mail as Mail
import mx.DateTime as DateTime
import email as email
import email.Message as Message
import email.Utils as Utils
import re as re

__exp = re.compile("\w+((-\w+)|(\.\w+)|(\_\w+))*\@[A-Za-z2-9]+((\.|-)[A-Za-z0-9]+)*\.[A-Za-z]{2,5}")

def isValidEmailAddress(emailAddress):
    """
    This method tests an email address for valid syntax as defined RFC 822
    ***Warning*** This method  will return False if Name and Address is past
    i.e. John Jones <john@jones.com>. The method only validates against the actual
    email address i.e. john@jones.com

    @param emailAddress: A string containing a email address to validate. Please see ***Warning*** for more
                         details
    @type addr: C{String}
    @return: C{Boolean}
    """
    if type(emailAddress) != str:
        return False

    emailAddress = emailAddress.strip()

    #XXX: Test id the address is in the form John test <john@test.com and handle it>
    #emailAddress = Utils.parseaddr(emailAddress)[1]

    if len(emailAddress) > 3:
        if __exp.match(emailAddress) is not None:
            return True

    return False

def emailAddressesAreEqual(emailAddressOne, emailAddressTwo):
    """
    This method tests whether two email addresses are the same.
    Addresses can be in the form john@jones.com or John Jones <john@jones.com>.
    The method strips off the username and <> brakets if they exist and just compares
    the actual email addresses for equality. It will not look to see if each
    address is RFC 822 compliant only that the strings match. Use C{message.isValidEmailAddress}
    to test for validity.

    @param emailAddressOne: A string containing a email address to compare.
    @type emailAddressOne: C{String}
    @param emailAddressTwo: A string containing a email address to compare.
    @type emailAddressTwo: C{String}
    @return: C{Boolean}
    """

    if type(emailAddressOne) != str or type(emailAddressTwo) != str:
        return False

    emailAddressOne = Utils.parseaddr(emailAddressOne)[1]
    emailAddressTwo = Utils.parseaddr(emailAddressTwo)[1]

    return emailAddressOne.lower() == emailAddressTwo.lower()


def hasValue(value):
    """
    This method determines if a String has one or more non-whitespace characters.
    This is useful in checking that a Subject or To address field was filled in with
    a useable value

    @param value: The String value to check against. The value can be None
    @type value: C{String}
    @return: C{Boolean}
    """
    if value is not None:
        test = value.strip()
        if len(test) > 0:
            return True

    return False

# XXX: Relook at this logic
def format_addr(addr):
    """
    This method formats an email address

    @param addr: The email address list to format
    @type addr: C{list}
    @return: C{string}
    """
    str = addr[0]
    if str != None and str != '':
        str = str + ' '

        str = str + '<' + addr[1] + '>'
        return str

    return addr[1]

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
        raise TypeError("Repository returned a MailMessage that was None")

    if messageObject['Date'] is not None:
        m.dateSent = DateTime.mktime(Utils.parsedate(messageObject['Date']))

    else:
        m.dateSent = None

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

    m.bccAddress = []
    for addr in Utils.getaddresses(messageObject.get_all('Bcc', [])):
        ea = Mail.EmailAddress()
        ea.emailAddress = format_addr(addr)
        m.bccAddress.append(ea)

    return m

def kindToMessageObject(mailMessage):
    """
    This method converts a email message string to
    a Chandler C{Mail.MailMessage} object

    @param messageObject: A C{email.Message} object representation of a mail message
    @type messageObject: C{email.Message}
    @return: C{Mail.MailMessage}
    """

    if not isinstance(mailMessage, Mail.MailMessage):
        raise TypeError("mailMessage must be an instance of Kind Mail.MailMessage")


    messageObject = Message.Message()

    messageObject['Date'] = Utils.formatdate(mailMessage.dateSent.ticks(), True)
    messageObject['Date Received'] = Utils.formatdate(mailMessage.dateReceived.ticks(), True)
    messageObject['Subject'] = mailMessage.subject

    messageObject['From'] = mailMessage.replyAddress.emailAddress

    to = []

    for address in mailMessage.toAddress:
        to.append(address.emailAddress)

    messageObject['To'] = ", ".join(to)

    del to

    cc = []

    for address in mailMessage.ccAddress:
        cc.append(address.emailAddress)

    messageObject['Cc'] = ", ".join(cc)

    del cc

    bcc = []

    for address in mailMessage.bccAddress:
        bcc.append(address.emailAddress)

    messageObject['Bcc'] = ", ".join(bcc)

    del bcc

    return messageObject


def kindToMessageText(mailMessage):
    """
    This method converts a email message string to
    a Chandler C{Mail.MailMessage} object

    @param messageObject: A C{email.Message} object representation of a mail message
    @type messageObject: C{email.Message}
    @return: C{Mail.MailMessage}
    """

    if not isinstance(mailMessage, Mail.MailMessage):
        raise TypeError("mailMessage must be an instance of Kind Mail.MailMessage")

    messageObject = kindToMessageObject(mailMessage)

    return messageObject.as_string()
