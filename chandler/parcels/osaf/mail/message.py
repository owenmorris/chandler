__revision__  = "$Revision$"
__date__      = "$Date$"
__copyright__ = "Copyright (c) 2005 Open Source Applications Foundation"
__license__   = "http://osafoundation.orgdler_0.1_license_terms.htm"

#python / mx imports
import email as email
import email.Header as Header
import email.Message as Message
import email.Utils as emailUtils
import mx.DateTime as DateTime
import logging as logging
import mimetypes

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

Attachment Notes:
-----------------------
First Pass:

Walk through parts:

   1. if part is an attachment determine correct type
      and add to mimeContainer of root email for all parts no matter how deep

   2. If part is text append to body (To do messages want to preserve levels of body text)

   3. If Part is text/* and not plain need th content-transfer-encoding and decode 
      as appropriate (should be handled by decode=1)

   4. If is message continue to walk for either attachments or tex

   To Do:
   ------
   1. Look in to what happens when parsing errors occur and how to handle

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


def populateHeader(messageObject, param, var, type='String'):
    #XXX: Need to document method

    if type == 'String':
        if utils.hasValue(var):
            messageObject[param] = var

    elif(type == 'EmailAddress'):
        if var is not None and utils.hasValue(var.emailAddress):
            messageObject[param] = Mail.EmailAddress.format(var)

def populateHeaders(mailMessage, messageObject):
    keys = mailMessage.headers.keys()

    for key in keys:
        messageObject[key] = mailMessage.headers[key]


def populateChandlerHeaders(mailMessage, messageObject):
    keys = mailMessage.chandlerHeaders.keys()

    for key in keys:
        messageObject[key] = mailMessage.chandlerHeaders[key]


def populateEmailAddresses(mailMessage, messageObject):
    #XXX: Need to document
    populateHeader(messageObject, 'From', mailMessage.fromAddress, 'EmailAddress')
    populateHeader(messageObject, 'Reply-To', mailMessage.replyToAddress, 'EmailAddress')

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

def messageObjectToKind(messageObject, messageText=None):
    """
    This method converts a email message string to
    a Chandler C{Mail.MailMessage} object

    @param messageObject: A C{email.Message} object representation of a mail message
    @type messageObject: C{email.Message}
    @return: C{Mail.MailMessage}
    """

    assert isinstance(messageObject, Message.Message), \
           "messageObject must be a Python email.Message.Message instance"

    m = Mail.MailMessage()

    # Save the original message text in a text blob
    if messageText is None:
        messageText = messageObject.as_string()

    #XXX: Save in a compressed format with a mime-type and perhaps a charset
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
        m.body = utils.strToText(m, "body", messageObject.get_payload().replace("\r", ""))

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

    assert isinstance(mailMessage, Mail.MailMessageMixin), \
           "mailMessage must be an instance of Kind Mail.MailMessage"

    messageObject = Message.Message()

    """Create a messageId if none exists"""
    if not utils.hasValue(mailMessage.messageId):
        mailMessage.messageId = utils.createMessageID()

    """Create a dateSent if none exists"""
    if not utils.hasValue(mailMessage.dateSentString):
        mailMessage.dateSent = DateTime.now()
        mailMessage.dateSentString = utils.dateTimeToRFC2882Date(mailMessage.dateSent)

    populateHeader(messageObject, 'Message-ID', mailMessage.messageId)
    populateHeader(messageObject, 'Date', mailMessage.dateSentString)
    populateEmailAddresses(mailMessage, messageObject)
    populateStaticHeaders(messageObject)
    populateChandlerHeaders(mailMessage, messageObject)
    populateHeaders(mailMessage, messageObject)
    populateHeader(messageObject, 'Subject', mailMessage.subject)

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

    assert isinstance(mailMessage, Mail.MailMessageMixin), \
    "mailMessage must be an instance of Kind Mail.MailMessage"

    messageObject = kindToMessageObject(mailMessage)
    messageText   = messageObject.as_string()

    #XXX: Want to compress this and store as well as set the mime type and charset
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
    __assignToKind(m, messageObject, 'From', 'EmailAddress', 'fromAddress')
    __assignToKind(m, messageObject, 'Reply-To', 'EmailAddress', 'replyToAddress')
    __assignToKind(m.toAddress, messageObject, 'To', 'EmailAddressList')
    __assignToKind(m.ccAddress, messageObject, 'Cc', 'EmailAddressList')
    __assignToKind(m.bccAddress, messageObject, 'Bcc', 'EmailAddressList')

    # Do not decode the message ID as it requires no i18n processing
    __assignToKind(m, messageObject, 'Message-ID', 'String', 'messageId', False)

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
        messageObject.replace_header(key, decodeHeader(messageObject[key]))

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


def __parseMessage(parentMIMEContainer, payload, body, level, messageText=None):
    """
        ToDo:
        -----
        1. Create a MailMessage Item
        2. If Root create an RFC822message Text Lob else add the MailMessage to the ParentContainer
        3. parse all headers
        2. Walk through if multipart
           a. if alternative or parallel then pass to parseMultipart will create
              a subcontainer and add the items

           Else:
             a. If root put payload Text in body else append the text to the body


        Notes:
        1, In the message itself is a multipart
        2. Body will be either passed along to sub type or
           if then message contains no payload will be 
           added to by this method

        Subtypes:
           message/delivery-status: Treat as text and add to the body
           message/disposition-notification-to: treat as text and add to body
           message/external-body: either ignore and log or add payload to body
           message/http: ignore
           message/partial: ignore
           message/rfc822: parse subparts get the subject and some headers and append to the message
                           body
    """

def __parseMultipart(parentMIMEContainer, payload, body, level):
    """
        Subtypes:
           multipart/alternative: find the text part and append to body or take first part
                                  and add to attachement list
           multipart/byteranges: ignore and log don't parse sub-parts
           multipart/digest: treat like a mixed type and parse subtypes which will be rfc-messages
           multipart/form-data: ignore and log  don't parse sub-parts
           multipart/mixed: ignore but parse sub-parts
           multipart/parallel: ignore but parse sub-parts treat like mixed for now
           multipart/related: ignore and log  don't parse sub-parts
           multipart/signed: ignore and log don't parse sub-parts
           multipart/encrypted: ignore and log don't parse sub-partsa
           multipart/report: treat like a mixed type and parse subtypes can be rfc-messages, text,
                             and or rfc-headers
    """


def __parseApplication(parentMIMEContainer, mimePart, num):
    """
        Handles unkown types
    """
    if mimePart.get_content_subtype() == "applefile":
        if __debug__:
            logging.warn("__parseApplication found type applefile ignoring")
        return

    app = Mail.MIMEBinary()
    app.mimeDesc = "APPLICATION"
    __parseMIMEPart(app, mimePart, num)

    parentMIMEContainer.append(app)


def __parseVideo(parentMIMEContainer, payload):
    vid = Mail.MIMEBinary()
    vid.mimeDesc = "VIDEO"

def __parseImage(parentMIMEContainer, payload):
    img = Mail.MIMEBinary()
    img.mimeDesc = "IMAGE"

def __parseAudio(parentMIMEContainer, payload):
    img = Mail.MIMEBinary()
    img.mimeDesc = "AUDIO"

def __parseText(parentMIMEContainer, payload, body, level):
    """
        Subtypes:
           text/enriched: treat as an attachment for now later add converted to text/plain
           text/html: treat as an attachment for now later add converted to text/plain
           text/plain: add to body
           text/rfc-headers: add to body as text/plain
           text/richtext: treat as an attachment for now later add converted to text/plain
           text/sgml: treat as an attachment for now later add converted to text/plain
    """

def __parseMIMEPart(mimeItem, mimePart, num):
    body = mimePart.get_payload(decode=1)

    mimeItem.filesize = len(body)
    mimeItem.filename = __getFileName(mimePart, num)

    #XXX: Need to account for charsets, and mime-type setting of body
    mimeItem.body     = utils.strToText(mimeItem, "body", body)
    mimeItem.mimeType = mimePart.get_content_type()


def __getFileName(mimePart, num):
    """
        This should handle all Unicode decoding of filename as well
    """
    filename = mimePart.get_filename()

    if filename:
        return filename

    """No Filename need to create an arbitrary name"""
    ext = mimetypes.guess_extension(mimePart.get_type())

    if not ext:
       ext = '.bin'

    return 'MIMEBinary-%s%s' % (num, ext)
