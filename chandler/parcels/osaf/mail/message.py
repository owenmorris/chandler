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
XXX: Do not check in till figure out repository error
XXX: get_param() returns a tuple
XXX: test_email.py, test_email_codecs.py in email package has good unicode examples
XXX: Look at Scrubber.py in Mailman package

   body = unicode(body, mcset).encode(lcset)
           except (LookupError, UnicodeError):
                       pass

return unicode(s, charset, "replace").encode(GlobalOptions.default_charset, "replace")


1. Encoding Email Address: Only encode name if present (I have example code)

To Do:
-------
1. Work with Apple Mail and see how it handle display of various message types and copy
2. Look at optimizations for Feedparser to prevent memory hogging (might tie in to twisted dataReceived)

Look at Prologue, Echo and i18n text complete / date complete

ARE THESES HANDLED BY THE EMAIL LIBRARY?
--------------------------------------

NOTE: Some protocols defines a maximum line length.  E.g. SMTP [RFC-
821] allows a maximum of 998 octets before the next CRLF sequence.
To be transported by such protocols, data which includes too long
segments without CRLF sequences must be encoded with a suitable
content-transfer-encoding.

Note that if the specified character set includes 8-bit characters
and such characters are used in the body, a Content-Transfer-Encoding
header field and a corresponding encoding on the data are required in
order to transmit the body via some mail transfer protocols, such as
SMTP [RFC-821].


In general, composition software should always use the "lowest common
denominator" character set possible.  For example, if a body contains
only US-ASCII characters, it SHOULD be marked as being in the US-
ASCII character set, not ISO-8859-1, which, like all the ISO-8859
family of character sets, is a superset of US-ASCII.  More generally,
if a widely-used character set is a subset of another character set,
and a body contains only characters in the widely-used subset, it
should be labelled as being in that subset.  This will increase the
chances that the recipient will be able to view the resulting entity
correctly.

Unrecognized subtypes of "text" should be treated as subtype "plain"
as long as the MIME implementation knows how to handle the charset.
Unrecognized subtypes which also specify an unrecognized charset
should be treated as "application/octet- stream".
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
    #XXX: Convert to unicode
    m.rfc2822Message = utils.strToText(m, "rfc2822Message", messageText)
    counter = utils.Counter()
    bodyBuffer = []
    buf = None

    if __verbose():
        if messageObject.has_key("Message-ID"):
            messageId = messageObject["Message-ID"]
        else:
            messageId = "<Unknown Message>"

        buf = ["Message: %s\n-------------------------------" % messageId]

    __parsePart(messageObject, m, bodyBuffer, counter, buf)

    """If the message has attachments set hasMimeParts to True"""
    if len(m.mimeParts) > 0:
        m.hasMimeParts = True

    #XXX: This will require i18n decoding
    #XXX: All body part should already be encoded in utf-8
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
            payload.encoding = constants.DEFAULT_CHARSET

        payloadStr = utils.textToStr(payload)

    except AttributeError:
        payloadStr = ""

    messageObject.set_payload(payloadStr)

    return messageObject


def kindToMessageText(mailMessage, saveMessage=False):
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
    #XXX: Convert to utf-8
    #XXX: I think we can reconstruct this structure at export and get rid of this
    #     save
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
            #XXX: What should happen if we get to this point we need a reply address
            logging.error("__assignToKind: invalid email address found %s: %s" % (key, addr[1]))

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
                #XXX: What should happen if we get to this point we need a reply address
                logging.error("__assignToKind: invalid email address found %s: %s" % (key, addr[1]))
    else:
        logging.error("__assignToKind: HEADER SLIPPED THROUGH")

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

            #XXX: This will require unicode conversion
            bodyBuffer.append(''.join(tmp))

        else:
            logging.warn("******WARNING****** message/rfc822 part not Multipart investigate")

    elif subtype == "delivery-status":
        #XXX: This is will need i18n decoding
        """Add the delivery status info to the message body """
        #XXX: assume us-ascii then covert to utf-8
        bodyBuffer.append(mimePart.as_string())
        return

    elif subtype == "disposition-notification-to":
        """Add the disposition-notification-to info to the message body"""
        #XXX: assume us-ascii then covert to utf-8
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
        logging.warn("******WARNING****** message/%s payload not multipart" % subtype)


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
            firstPart = None

            for part in payload:
                if part.get_content_type() == "text/plain":
                    __handleText(part, parentMIMEContainer, bodyBuffer, counter, buf, level)
                    foundText = True
                    break

                if firstPart is None and not part.is_multipart():
                    """A multipart/alternative container should have
                       at least one part that is not multipart and
                       is text based (plain, html, rtf) for display
                    """
                    firstPart = part

            if not foundText and firstPart is not None:
                if firstPart.get_content_maintype() == "text":
                    __handleText(firstPart, parentMIMEContainer, bodyBuffer, counter, buf, level)
                else:
                    __handleBinary(firstPart, parentMIMEContainer, counter, buf, level)
        else:
            logging.warn("******WARNING****** multipart/alternative has no payload")

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

def __handleText(mimePart, parentMIMEContainer, bodyBuffer, counter, buf, level):
    subtype = mimePart.get_content_subtype()

    if __verbose():
        __trace("text/%s" % subtype, buf, level)

    """Get the attachment data"""
    body = mimePart.get_payload(decode=1)
    assert isinstance(body, str) , "__handleText body is not a String"

    size = len(body)

    #XXX: If there is an encoding then decode first then store
    content_charset = mimePart.get_content_charset(None)

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
    #XXX: Does this handle all Unicode decoding of filename as well?
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
        strBuffer = [mimePart.get("Message-ID", "Unknown Message ID")]
        handled = False

        for defect in mimePart.defects:
            """Just get the class name strip the package path"""
            defectName = str(defect.__class__).split(".").pop()

            if not handled and \
              (defectName == "MultipartInvariantViolationDefect" or \
               defectName == "NoBoundaryInMultipartDefect" or \
               defectName == "StartBoundaryNotFoundDefect"):

                """
                   The Multipart Body of the message is corrupted or
                   inaccurate(Spam?) convert the payload to a text part.
                """
                mimePart._payload = "".join(mimePart._payload)
                mimePart.replace_header("Content-Type", "text/plain")
                handled = True

            strBuffer.append(defectName)

        logging.warn("*****WARNING**** Mail Parsing defect: %s" % ", ".join(strBuffer))

def __appendHeader(mimePart, buffer, header):
    if mimePart.has_key(header):
        #XXX: This will need i18n unicode encoding
        buffer.append("%s: %s\n" % (header, decodeHeader(mimePart[header])))

def __verbose():
    return __debug__ and constants.VERBOSE

def __trace(contype, buf, level):
    buf.append("%s %s" % (level * "  ", contype))
