__revision__  = "$Revision$"
__date__      = "$Date$"
__copyright__ = "Copyright (c) 2004 Open Source Applications Foundation"
__license__   = "http://osafoundation.org/Chandler_0.1_license_terms.htm"

import osaf.contentmodel.mail.Mail as Mail
import chandlerdb.util.UUID as UUID
import repository.persistence.XMLRepositoryView as XMLRepositoryView
import mx.DateTime as DateTime
import email as email
import email.Message as Message
import email.Utils as Utils
import common as common
import logging as logging


def dateTimeToRFC2882Date(dateTime):
    """Converts a C{mx.DateTime} objedt ot a
       RFC2882 Date String

       @param dateTime: a C{mx.DateTime} instance
       @type dateTime: C{mx.DateTime}

       @return: RFC2882 Date String
    """
    return Utils.formatdate(dateTime.ticks(), True)

def createMessageID():
    """Creates a unique message id
       @return: String containing the unique message id"""
    return Utils.make_msgid()

def getToAddressesFromMailMessage(mailMessage):
    assert isinstance(mailMessage, Mail.MailMessageMixin), "mailMessage must be an instance of Kind Mail.MailMessage"
    to_addrs = []

    for address in mailMessage.toAddress:
        to_addrs.append(address.emailAddress)

    return to_addrs

def getFromAddressFromMailMessage(mailMessage):
    assert isinstance(mailMessage, Mail.MailMessageMixin), "mailMessage must be an instance of Kind Mail.MailMessage"

    if mailMessage.replyToAddress is not None:
        return mailMessage.replyToAddress.emailAddress

    elif mailMessage.fromAddress is not None:
        return mailMessage.fromAddress.emailAddress

    return None


def hasValue(value):
    """
    This method determines if a String has one or more non-whitespace characters.
    This is useful in checking that a Subject or To address field was filled in with
    a useable value

    @param value: The String value to check against. The value can be None
    @type value: C{String}
    @return: C{Boolean}
    """
    if __isString(value) and len(value.strip()) > 0:
        return True

    return False

def isPlainTextContentType(contentType):
    """Determines if the content-type is 'text/plain'
       @param contentType: content type string
       @type contentType: C{str}

       @return bool: True if content-type='text/plain'
    """
    if __isString(contentType) and contentType.lower().strip() == common.MIME_TEXT_PLAIN:
        return True

    return False

def createChandlerHeader(postfix):
    """Creates a chandler header with postfix provided"""
    assert hasValue(postfix), "You must pass a String"

    return common.CHANDLER_HEADER_PREFIX + postfix

def isChandlerHeader(header):
    """Returns true if the header is Chandler defined header"""
    assert hasValue(header), "You must pass a String"

    if header.startswith(common.CHANDLER_HEADER_PREFIX):
        return True

    return False

def messageTextToKind(messageText):
    """
    This method converts a email message string to
    a Chandler C{Mail.MailMessage} object

    @param messageText: A string representation of a mail message
    @type messageText: string
    @return: C{Mail.MailMessage}
    """

    assert isinstance(messageText, str), "messageText must be a String"

    return messageObjectToKind(email.message_from_string(messageText), messageText)

def messageObjectToKind(messageObject, messageText=None):
    """
    This method converts a email message string to
    a Chandler C{Mail.MailMessage} object

    @param messageObject: A C{email.Message} object representation of a mail message
    @type messageObject: C{email.Message}
    @return: C{Mail.MailMessage}
    """

    assert isinstance(messageObject, Message.Message), "messageObject must be a Python email.Message.Message instance"

    m = Mail.MailMessage()

    assert m is not None, "Repository returned a MailMessage that was None"

    if messageText is None:
        messageText = messageObject.as_string()

    # Save the original message text in a text blob
    m.rfc2822Message = strToText(m, "rfc2822Message", messageText)

    date = messageObject['Date']

    if date is not None:
        parsed = Utils.parsedate(date)

        """It is a non-rfc date string"""
        if parsed is None:
            if __debug__:
                logging.warn("Message contains a Non-RFC Compliant Date format")

            m.dateSent = common.getEmptyDate()

        else:
            m.dateSent = DateTime.mktime(parsed)

        m.dateSentString = date
        del messageObject['Date']

    else:
        m.dateSent = common.getEmptyDate()
        m.dateSentString = ""

    m.dateReceived = DateTime.now()

    __assignToKind(m, messageObject, 'Subject', 'String', 'subject')
    __assignToKind(m, messageObject, 'Content-Type', 'String', 'contentType')
    __assignToKind(m, messageObject, 'Content-Length', 'String', 'contentLength')
    __assignToKind(m, messageObject, 'Content-Transfer-Encoding', 'String', 'contentTransferEncoding')
    __assignToKind(m, messageObject, 'Mime-Version', 'String', 'mimeVersion')
    __assignToKind(m, messageObject, 'Message-ID', 'String', 'messageId')
    __assignToKind(m, messageObject, 'Return-Path', 'String', 'returnPath')
    __assignToKind(m, messageObject, 'In-Reply-To', 'String', 'inReplyTo')
    __assignToKind(m, messageObject, 'From', 'EmailAddress', 'fromAddress')
    __assignToKind(m, messageObject, 'Reply-To', 'EmailAddress', 'replyToAddress')
    __assignToKind(m.toAddress, messageObject, 'To', 'EmailAddressList')
    __assignToKind(m.ccAddress, messageObject, 'Cc', 'EmailAddressList')
    __assignToKind(m.bccAddress, messageObject, 'Bcc', 'EmailAddressList')
    __assignToKind(m.references, messageObject, 'References', 'StringList')
    __assignToKind(m.received, messageObject, 'Received', 'StringList')

    m.chandlerHeaders = {}
    m.additionalHeaders = {}

    for (key, val) in messageObject.items():

        if isChandlerHeader(key):
            m.chandlerHeaders[key] =  val

        else:
            m.additionalHeaders[key] = val

        try:
            del messageObject[key]

        except KeyError:
            logging.error("in osaf.mail.message.messageObjectToKind: KEY ERROR")

    if messageObject.is_multipart():
        mimeParts = messageObject.get_payload()
        found = False
        m.hasMimeParts = True
        m.mimeParts = []

        for mimePart in mimeParts:
            if isPlainTextContentType(mimePart.get_content_type()):
                # Note: while grabbing the body, strip all CR
                m.body = strToText(m, "body",
                 mimePart.get_payload().replace("\r", ""))
                found = True

        if not found:
            m.body = strToText(m, "body", common.ATTACHMENT_BODY_WARNING)

    else:
        # Note: while grabbing the body, strip all CR
        m.body = strToText(m, "body",
         messageObject.get_payload().replace("\r", ""))

    return m

def kindToMessageObject(mailMessage):
    """
    This method converts a email message string to
    a Chandler C{Mail.MailMessage} object

    @param messageObject: A C{email.Message} object representation of a mail message
    @type messageObject: C{email.Message}

    @return: C{Message.Message}
    """

    assert isinstance(mailMessage, Mail.MailMessageMixin), "mailMessage must be an instance of Kind Mail.MailMessage"

    #XXX: To do figure out in relpy to / recieved  / references logic
    messageObject = Message.Message()

    if not hasValue(mailMessage.messageId):
        mailMessage.messageId = createMessageID()

    __populateParam(messageObject, 'Message-ID', mailMessage.messageId)

    messageObject['User-Agent'] = common.CHANDLER_USERAGENT

    __populateParam(messageObject, 'Date', mailMessage.dateSentString)
    __populateParam(messageObject, 'Subject', mailMessage.subject)
    __populateParam(messageObject, 'Content-Type', mailMessage.contentType)
    __populateParam(messageObject, 'Content-Length', mailMessage.contentLength)
    __populateParam(messageObject, 'Content-Transfer-Encoding', mailMessage.contentTransferEncoding)
    __populateParam(messageObject, 'MIME-Version', mailMessage.mimeVersion)
    __populateParam(messageObject, 'Return-Path', mailMessage.returnPath)
    __populateParam(messageObject, 'In-Reply-To', mailMessage.inReplyTo)

    if len(mailMessage.references) > 0:
        messageObject['References'] = " ".join(mailMessage.references)

    #XXX: This will be a special case because we need multiple received headers
    if len(mailMessage.received) > 0:
        messageObject['Received'] = " ".join(mailMessage.received)

    keys = mailMessage.chandlerHeaders.keys()

    for key in keys:
        messageObject[key] = mailMessage.chandlerHeaders[key]

    keys = mailMessage.additionalHeaders.keys()

    for key in keys:
        messageObject[key] = mailMessage.additionalHeaders[key]

    try:
        payload = mailMessage.body
    except AttributeError:
        payloadStr = ""
    else:
        payloadStr = textToStr(payload)
    messageObject.set_payload(payloadStr)

    __populateParam(messageObject, 'From', mailMessage.fromAddress, 'EmailAddress')
    __populateParam(messageObject, 'Reply-To', mailMessage.replyToAddress, 'EmailAddress')

    to = []

    for address in mailMessage.toAddress:
        if hasValue(address.emailAddress):
            to.append(Mail.EmailAddress.format(address))

    if len(to) > 0:
        messageObject['To'] = ", ".join(to)

    cc = []

    for address in mailMessage.ccAddress:
        if hasValue(address.emailAddress):
            cc.append(Mail.EmailAddress.format(address))

    if len(cc) > 0:
        messageObject['Cc'] = ", ".join(cc)

    bcc = []

    for address in mailMessage.bccAddress:
        if hasValue(address.emailAddress):
             bcc.append(Mail.EmailAddress.format(address))

    if len(bcc) > 0:
        messageObject['Bcc'] = ", ".join(bcc)

    return messageObject


def kindToMessageText(mailMessage, saveMessage=True):
    """
    This method converts a email message string to
    a Chandler C{Mail.MailMessage} object

    @param messageObject: A C{email.Message} object representation of a mail message
    @type messageObject: C{email.Message}
    @param saveMessage: save the message text converted from the C{email.Message} in the mailMessage.rfc2882Message
                        attribute
    @type saveMessage: C{Boolean}
    @return: C{str}
    """

    assert isinstance(mailMessage, Mail.MailMessageMixin), "mailMessage must be an instance of Kind Mail.MailMessage"
    messageObject = kindToMessageObject(mailMessage)

    messageText = messageObject.as_string()

    if saveMessage:
        mailMessage.rfc2882Message = strToText(mailMessage, "rfc2822Message", messageText)

    return messageText


def strToText(contentItem, attribute, string):
    """Converts a C{str} to C{Text}"""
    if not __isString(string):
        return None

    return contentItem.getAttributeAspect(attribute, 'type').makeValue(string, indexed=False)



def textToStr(text):
    """Converts a C{Text} to a C{str}"""
    assert isinstance(text, XMLRepositoryView.XMLText), "Must pass a XMLRepositoryView.XMLText instance"

    reader = text.getReader()
    string = reader.read()
    reader.close()

    return string

def getMailMessage(UUID):
    """Returns a C{MailMessage} from its C{UUID}"""
    assert isinstance(UUID, UUID.UUID), "Must pass a UUID.UUID object"

    mailMessageKind = Mail.MailMessage.getKind()
    return mailMessageKind.findUUID(UUID)


def __populateParam(messageObject, param, var, type='String'):

    if type == 'String':
        if hasValue(var):
            messageObject[param] = var

    elif(type == 'EmailAddress'):
        if var is not None and hasValue(var.emailAddress):
            messageObject[param] = Mail.EmailAddress.format(var)


def __assignToKind(kindVar, messageObject, key, type, attr = None):

    if type == "String":
        if messageObject[key] is not None:
            setattr(kindVar, attr, messageObject[key])

    # XXX: This logic will need to be expanded
    elif type == "StringList":
        if messageObject[key] is not None:
            kindVar.append(messageObject[key])

    elif type == "EmailAddress":
        if messageObject[key] is not None:
            addr = Utils.parseaddr(messageObject[key])

            keyArgs = {}
            if hasValue(addr[0]):
                keyArgs['fullName'] = addr[0]

            # Use any existing EmailAddress, but don't update them
            #  because that will cause the item to go stale in the UI thread.
            ea = Mail.EmailAddress.getEmailAddress(addr[1], **keyArgs)

            if ea is not None:
                setattr(kindVar, attr, ea)

            elif __debug__:
                logging.error("in osaf.mail.message.__assignToKind: invalid email address found")

    elif type == "EmailAddressList":
        if messageObject[key] is not None:
            for addr in Utils.getaddresses(messageObject.get_all(key, [])):
                keyArgs = {}
                if hasValue(addr[0]):
                    keyArgs['fullName'] = addr[0]

                # Use any existing EmailAddress, but don't update them
                #  because that will cause the item to go stale in the UI thread.
                ea = Mail.EmailAddress.getEmailAddress(addr[1], **keyArgs)
                if ea is not None:
                    kindVar.append(ea)

                elif __debug__:
                    logging.error("in osaf.mail.message.__assignToKind: invalid email address found")
    else:
        logging.error("in osaf.mail.message.__assignToKind: HEADER SLIPPED THROUGH")

    try:
       del messageObject[key]

    except KeyError:
        logging.error("in osaf.mail.message.__assignToKind: KEY ERROR")

def __isString(var):
    if isinstance(var, (str, unicode)):
        return True

    return False

