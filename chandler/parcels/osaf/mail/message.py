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

To Do:
-------
1. Work with Apple Mail and see how it handle display of various message types and copy
2. Look at optimizations for Feedparser to prevent memory hogging
3. Add back Unicode support

Look at Prologue, Echo and i18n text complete / date complete
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

    assert len(messageObject.keys()) > 0, \
           "messageObject data is not a valid RFC2882 message"

    m = Mail.MailMessage()

    # Save the original message text in a text blob
    if messageText is None:
        messageText = messageObject.as_string()


    #XXX:Could compress at a later date
    m.rfc2822Message = utils.strToText(m, "rfc2822Message", messageText)
    counter = utils.Counter()
    bodyBuffer = []
    buf = None

    __checkForDefects(messageObject)

    if __verbose():
        if messageObject.has_key("Message-ID"):
            messageId = messageObject["Message-ID"]
        else:
            messageId = "<Unknown Message>"

        buf = ["Message: %s\n-------------------------------" % messageId]

    __parsePart(messageObject, m, bodyBuffer, counter, buf)

    m.body = utils.strToText(m, "body", '\n'.join(bodyBuffer).replace("\r", ""))

    __parseHeaders(messageObject, m)

    if __verbose():
        logging.warn("\n\n%s\n\n" % '\n'.join(buf))

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

        #XXX: Temp hack this should be fixed in GUI level
        #     investigate with Andi and Bryan
        if payload.encoding is None:
            payload.encoding = "utf-8"

        payloadStr = utils.textToStr(payload)

    except AttributeError:
        payloadStr = ""

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

    #XXX: Can compress as well
    if saveMessage:
        mailMessage.rfc2882Message = utils.strToText(mailMessage, "rfc2822Message", \
                                                     messageText)

    return messageText


def __parseHeaders(messageObject, m):

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


def __parsePart(mimePart, parentMIMEContainer, bodyBuffer, counter, buf, level=0):
    __checkForDefects(mimePart)

    maintype  = mimePart.get_content_maintype()

    if maintype == "message":
        __handleMessage(mimePart, parentMIMEContainer, bodyBuffer, counter, buf, level)

    elif maintype == "multipart":
        __handleMultipart(mimePart, parentMIMEContainer, bodyBuffer, counter, buf, level)

    elif maintype == "text":
        __handleText(mimePart, parentMIMEContainer, bodyBuffer, counter, buf, level)

    else:
        __handleBinary(mimePart, parentMIMEContainer,  counter, buf, level)


def __handleMessage(mimePart, parentMIMEContainer, bodyBuffer, counter, buf, level):
    subtype   = mimePart.get_content_subtype()
    multipart = mimePart.is_multipart()

    if __verbose():
        __trace("message/%s" % subtype, buf, level)

    """If the message is multipart then pass decode=False to
    get_poyload otherwise pass True"""
    payload = mimePart.get_payload(decode=not multipart)
    assert payload is not None, "__handleMessage payload is None"

    if subtype == "rfc822":
        if multipart:
            sub = mimePart.get_payload()[0]
            assert sub is not None, "__handleMessage sub is None"

            tmp = []

            tmp.append("\n")
            __appendHeader(sub, tmp, "From")
            __appendHeader(sub, tmp, "Reply-To")
            __appendHeader(sub, tmp, "Date")
            __appendHeader(sub, tmp, "To")
            __appendHeader(sub, tmp, "Cc")
            __appendHeader(sub, tmp, "Subject")
            tmp.append("\n")

            bodyBuffer.append(''.join(tmp))

        else:
            logging.warn("******WARNING****** message/rfc822 part not Multipart investigate")

    elif subtype == "delivery-status":
        #XXX: This is will need i18n decoding
        """Add the delivery status info to the message body """
        bodyBuffer.append(mimePart.as_string())
        return

    elif subtype == "disposition-notification-to":
        """Add the disposition-notification-to info to the message body"""
        #XXX: This is will need i18n decoding
        bodyBuffer.append(mimePart.as_string())
        return

    elif subtype == "external-body":
        logging.warn("Chandler Mail Service does not support message/external-body at this time")
        return

    elif subtype == "http":
        logging.warn("Chandler Mail Service does not support message/http at this time")
        return

    elif subtype == "partial":
        logging.warn("Chandler Mail Service does not support message/partial at this time")
        return

    if multipart:
        for part in payload:
            __parsePart(part, parentMIMEContainer, bodyBuffer, counter, buf, level+1)

    else:
        #XXX: Do not think this case exists investigate
        bodyBuffer.append(payload)


def __handleMultipart(mimePart, parentMIMEContainer, bodyBuffer, counter, buf, level):
    subtype   = mimePart.get_content_subtype()
    multipart = mimePart.is_multipart()

    if __verbose():
        __trace("multipart/%s" % subtype, buf, level)

    """If the message is multipart then pass decode=False to
    get_poyload otherwise pass True"""
    payload = mimePart.get_payload(decode=not multipart)
    assert payload is not None, "__handleMultipart payload is None"

    if subtype == "alternative":
        """An alternative container should always have at least one part"""
        if len(payload) > 0:
            foundText = False

            for part in payload:
                if part.get_content_type() == "text/plain":
                    #XXX: This needs i18n decoding
                    payload = part.get_payload(decode=1)
                    assert payload is not None, "__handleMultipart alternative payload is None"

                    bodyBuffer.append(payload)
                    foundText = True
                    break

            #XXX: This can be condensed for performance efficiency
            if not foundText:
                for part in payload:
                    """A multipart/alternative container should have
                       at least one part that is not multipart and
                       is text based (plain, html, rtf) for display
                    """
                    if not part.is_multipart():
                        if part.get_content_main_type() == "text":
                            __handleText(part, parentContainer, bodyBuffer, counter, buf, level)
                        else:
                            __handleBinary(part, parentContainer, counter, buf, level)

                        break

    elif subtype == "byteranges":
        logging.warn("Chandler Mail Service does not support multipart/byteranges at this time")
        return

    elif subtype == "form-data":
        logging.warn("Chandler Mail Service does not support multipart/form-data at this time")
        return

    elif subtype == "signed":
        logging.warn("Chandler Mail Service does not support multipart/signed at this time")
        return

    elif subtype == "encrypted":
        logging.warn("Chandler Mail Service does not support multipart/encrypted at this time")
        return

    else:
        for part in payload:
            __parsePart(part, parentMIMEContainer, bodyBuffer, counter, buf, level+1)


def __handleBinary(mimePart, parentMIMEContainer, counter, buf, level):
    contype = mimePart.get_content_type()

    if __verbose():
        __trace(contype, buf, level)

    # skip AppleDouble resource files per RFC1740
    if contype == "application/applefile":
        return

    mimeBinary = Mail.MIMEBinary()

    """Get the attachments data"""
    body = mimePart.get_payload(decode=1)
    assert body is not None, "__handleBinary body is None"

    mimeBinary.filesize = len(body)
    mimeBinary.filename = __getFileName(mimePart, counter)
    mimeBinary.mimeType = contype

    """Try to figure out what the real mimetype is"""
    if contype == "application/octet-stream" and \
       not mimeBinary.filename.endswith(".bin"):
       result = mimetypes.guess_type(mimeBinary.filename, strict=False)
       if result[0] is not None:
             mimeBinary.mimeType = result[0]

    mimeBinary.body = utils.dataToBinary(mimeBinary, "body", body)

    parentMIMEContainer.mimeParts.append(mimeBinary)
    parentMIMEContainer.hasMimeParts = True

def __handleText(mimePart, parentMIMEContainer, bodyBuffer, counter, buf, level):
    subtype = mimePart.get_content_subtype()

    if __verbose() and size > 0:
        __trace("text/%s" % subtype, buf, level)

    """Get the attachment data"""
    body = mimePart.get_payload(decode=1)
    assert body is not None, "__handleText body is None"

    size = len(body)


    #XXX: If there is an encoding then decode first then store
    #encoding = mimePart.get
    charset  = mimePart.get_charset()
    content_charset  = mimePart.get_content_charset()

    if subtype == "plain" or subtype == "rfc822-headers":
        #XXX: this requires i18n decoding
        size > 0 and bodyBuffer.append(body)

    else:
        mimeText = Mail.MIMEText()

        mimeText.mimeType = mimePart.get_content_type()
        mimeText.filesize = len(body)
        mimeText.filename = __getFileName(mimePart, counter)
        mimeText.body = utils.strToText(mimeText, "body", body)

        parentMIMEContainer.mimeParts.append(mimeText)
        parentMIMEContainer.hasMimeParts = True

def __getFileName(mimePart, counter):
    #XXX: This should handle all Unicode decoding of filename as well
    filename = mimePart.get_filename()

    if filename:
        return filename

    """No Filename need to create an arbitrary name"""
    ext = mimetypes.guess_extension(mimePart.get_content_type())

    if not ext:
       ext = '.bin'

    return 'Attachment-%s%s' % (counter.nextValue(), ext)

def __checkForDefects(mimePart):
    if len(mimePart.defects) > 0:
        strBuffer = []

        for defect in mimePart.defects:
            strBuffer.append(str(defect.__class__).split(".").pop())

        logging.warn("*****WARNING**** the following Mail Parsing defects \
                     found: %s" % ", ".join(strBuffer))

def __appendHeader(mimePart, buffer, header):
    if mimePart.has_key(header):
        buffer.append("%s: %s\n" % (header, decodeHeader(mimePart[header])))

def __verbose():
    return __debug__ and constants.VERBOSE

def __trace(contype, buf, level):
    buf.append("%s %s" % (level * "  ", contype))
