__revision__  = "$Revision$"
__date__      = "$Date$"
__copyright__ = "Copyright (c) 2005 Open Source Applications Foundation"
__license__   = "http://osafoundation.org/Chandler_0.1_license_terms.htm"

#python / mx imports
import email as email
import email.Header as Header
import email.Message as Message
import email.Utils as emailUtils
import mx.DateTime as DateTime
import logging as logging

#Chandler imports
import osaf.contentmodel.mail.Mail as Mail
import chandlerdb.util.UUID as UUID

#Chandler Mail Service imports
import constants as constants
import utils as utils

"""
Notes:
1. Encoding Email Address: Only encode name if present

   TO DO:
      Clean up what is decoded and what is does not need to be decoded
      Need to decode values with in params ie. filename
   Yes: 
   1. Email Address name
   2. Subject

   That's it
   No: 
   Received headers
   Content-Type or Content-Disposition ect
"""

def decodeHeader(header, charset=constants.DEFAULT_CHARSET):
    try:
        decoded    = Header.make_header(Header.decode_header(header))
        unicodeStr = decoded.__unicode__()
        line       = emailUtils.UEMPTYSTRING.join(unicodeStr.splitlines())

        return line.encode(charset, 'replace')

    except(UnicodeError, LookupError):
        return emailUtils.EMPTYSTRING.join(header.splitlines())

def createChandlerHeader(postfix):
    """Creates a chandler header with postfix provided"""
    assert utils.hasValue(postfix), "You must pass a String"

    return constants.CHANDLER_HEADER_PREFIX + postfix

def isChandlerHeader(header):
    """Returns true if the header is Chandler defined header"""
    assert utils.hasValue(header), "You must pass a String"

    if header.startswith(constants.CHANDLER_HEADER_PREFIX):
        return True

    return False

def isPlainTextContentType(contentType):
    """Determines if the content-type is 'text/plain'
       @param contentType: content type string
       @type contentType: C{str}

       @return bool: True if content-type='text/plain'
    """
    #XXX: is this needed
    if utils.isString(contentType) and contentType.lower().strip() == constants.MIME_TEXT_PLAIN:
        return True

    return False

def populateStaticHeaders(messageObject):
    """Populates the static mail headers"""
    #XXX: Need to document method
    #XXX: Will be expanded when i18n is in place

    if not messageObject.has_key('User-Agent'):
        messageObject['User-Agent'] = constants.CHANDLER_USERAGENT

    if not messageObject.has_key('MIME-Version'):
        messageObject['MIME-Version'] = "1.0"

    if not messageObject.has_key('Content-Type'):
        messageObject['Content-Type'] = "text/plain; charset=us-ascii; format=flowed"

    if not messageObject.has_key('Content-Transfer-Encoding'):
       messageObject['Content-Transfer-Encoding'] = "7bit"


def populateParam(messageObject, param, var, type='String'):
    #XXX: Need to document method

    if type == 'String':
        if utils.hasValue(var):
            messageObject[param] = var

    elif(type == 'EmailAddress'):
        if var is not None and utils.hasValue(var.emailAddress):
            messageObject[param] = Mail.EmailAddress.format(var)

def populateEmailAddresses(mailMessage, messageObject):
    #XXX: Need to document
    populateParam(messageObject, 'From', mailMessage.fromAddress, 'EmailAddress')
    populateParam(messageObject, 'Reply-To', mailMessage.replyToAddress, 'EmailAddress')

    populateEmailAddressList(mailMessage.toAddress, messageObject, 'To')
    populateEmailAddressList(mailMessage.ccAddress, messageObject, 'Cc')

def populateEmailAddressList(emailAddressList, messageObject, key):
    #XXX: Need to document
    addrs = []

    for address in emailAddressList:
        if utils.hasValue(address.emailAddress):
            addrs.append(Mail.EmailAddress.format(address))

    if len(addrs) > 0:
        messageObject[key] = ", ".join(addrs)


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

def messageObjectToKind(messageObject, messageText=None, root=True):
    """
    This method converts a email message string to
    a Chandler C{Mail.MailMessage} object

    @param messageObject: A C{email.Message} object representation of a mail message
    @type messageObject: C{email.Message}
    @return: C{Mail.MailMessage}
    """

    assert isinstance(messageObject, Message.Message), "messageObject must be a Python email.Message.Message instance"

    m = Mail.MailMessage()

    if messageText is None:
        messageText = messageObject.as_string()

    # Save the original message text in a text blob
    #XXX: Only save this if it is the root element
    if root:
        m.rfc2822Message = utils.strToText(m, "rfc2822Message", messageText)

    if messageObject.is_multipart():
        mimeParts = messageObject.get_payload()
        found = False
        m.hasMimeParts = True
        m.mimeParts = []

        for mimePart in mimeParts:
            if isPlainTextContentType(mimePart.get_content_type()):
                # Note: while grabbing the body, strip all CR
                m.body = utils.strToText(m, "body", mimePart.get_payload().replace("\r", ""))
                found = True

        if not found:
            m.body = utils.strToText(m, "body", constants.ATTACHMENT_BODY_WARNING)

    else:
        # Note: while grabbing the body, strip all CR
        m.body = utils.strToText(m, "body",
         messageObject.get_payload().replace("\r", ""))

    __parseHeaders(m, messageObject)

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

    messageObject = Message.Message()

    """Create a messageId if none exists"""
    if not utils.hasValue(mailMessage.messageId):
        mailMessage.messageId = utils.createMessageID()

    """Create a dateSent if none exists"""
    if not utils.hasValue(mailMessage.dateSentString):
        mailMessage.dateSent = DateTime.now()
        mailMessage.dateSentString = utils.dateTimeToRFC2882Date(mailMessage.dateSent)

    populateParam(messageObject, 'Message-ID', mailMessage.messageId)
    populateParam(messageObject, 'Date', mailMessage.dateSentString)

    populateEmailAddresses(mailMessage, messageObject)
    populateStaticHeaders(messageObject)

    keys = mailMessage.headers.keys()

    for key in keys:
        messageObject[key] = mailMessage.headers[key]

    keys = mailMessage.chandlerHeaders.keys()

    for key in keys:
        messageObject[key] = mailMessage.chandlerHeaders[key]

    populateParam(messageObject, 'Subject', mailMessage.subject)

    try:
        payload = mailMessage.body
    except AttributeError:
        payloadStr = ""
    else:
        payloadStr = utils.textToStr(payload)

    messageObject.set_payload(payloadStr)

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

    #XXX: Want to compress this and store as a binary type of lob
    if saveMessage:
        mailMessage.rfc2882Message = utils.strToText(mailMessage, "rfc2822Message", messageText)

    return messageText


def __parseHeaders(m, messageObject):

    date = messageObject['Date']

    if date is not None:
        #XXX: look at using Utils.parsedate_tz
        parsed = emailUtils.parsedate(date)

        """It is a non-rfc date string"""
        if parsed is None:
            if __debug__:
                logging.warn("Message contains a Non-RFC Compliant Date format")

            #Set the sent date to the current Date
            m.dateSent = DateTime.now()

        else:
            m.dateSent = DateTime.mktime(parsed)

        ##XXX:  Do we need this the tz could be preserved
        m.dateSentString = date
        del messageObject['Date']

    else:
        m.dateSent = utils.getEmptyDate()
        m.dateSentString = ""

    __assignToKind(m, messageObject, 'Subject', 'String', 'subject')
    # Do not decode the message ID as it requires no i18n processing
    __assignToKind(m, messageObject, 'Message-ID', 'String', 'messageId', False)
    __assignToKind(m, messageObject, 'From', 'EmailAddress', 'fromAddress')
    __assignToKind(m, messageObject, 'Reply-To', 'EmailAddress', 'replyToAddress')
    __assignToKind(m.toAddress, messageObject, 'To', 'EmailAddressList')
    __assignToKind(m.ccAddress, messageObject, 'Cc', 'EmailAddressList')
    __assignToKind(m.bccAddress, messageObject, 'Bcc', 'EmailAddressList')

    m.chandlerHeaders = {}
    m.headers = {}

    #XXX: Will want to selectively decodeHeaders for i18n support see RFC: 2231 
    #     for more info

    for (key, val) in messageObject.items():
        if isChandlerHeader(key):
            m.chandlerHeaders[key] = val

        else:
            m.headers[key] = val

        del messageObject[key]



def __assignToKind(kindVar, messageObject, key, type, attr=None, decode=True):

    try:
        """ Test that a key exists and its value is not None """
        if messageObject[key] is None:
            return
    except KeyError:
        return

    if decode:
        __decodeHeader(messageObject, key)

    if type == "String":
        setattr(kindVar, attr, messageObject[key])

    # XXX: This logic will need to be expanded
    elif type == "StringList":
        kindVar.append(messageObject[key])

    elif type == "EmailAddress":
        keyArgs = {}
        addr = emailUtils.parseaddr(messageObject[key])

        if utils.hasValue(addr[0]):
            keyArgs['fullName'] = addr[0]

        # Use any existing EmailAddress, but don't update them
        #  because that will cause the item to go stale in the UI thread.
        ea = Mail.EmailAddress.getEmailAddress(addr[1], **keyArgs)

        if ea is not None:
            setattr(kindVar, attr, ea)

        elif __debug__:
            logging.error("in osaf.mail.message.__assignToKind: invalid email address found")

    elif type == "EmailAddressList":
        for addr in emailUtils.getaddresses(messageObject.get_all(key, [])):
            keyArgs = {}

            if utils.hasValue(addr[0]):
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

    del messageObject[key]

def __decodeHeader(messageObject, key):
    messageObject.replace_header(key, decodeHeader(messageObject[key]))

def __parseMessage(parentMIMEContainer):
    """
        need the parent container passed
        with. The container can be a rfc822 message
        or multipart container (alternative unlikely, multipart/report)

    """

def __parseMultipart(parentMIMEContainer):
    """
        Disregard any multipart container
        that is not required (alternative)

        Need the parent which will be the
        message that the multipart c
    """

def __parseApplication():
    """
        Handles unkown types
    """

def __parseVideo():
    pass

def __parseImage():
    pass

def __parseText():
    pass

def __parseAudio():
    pass


