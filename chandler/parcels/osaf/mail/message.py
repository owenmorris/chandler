#   Copyright (c) 2005-2006 Open Source Applications Foundation
#
#   Licensed under the Apache License, Version 2.0 (the "License");
#   you may not use this file except in compliance with the License.
#   You may obtain a copy of the License at
#
#       http://www.apache.org/licenses/LICENSE-2.0
#
#   Unless required by applicable law or agreed to in writing, software
#   distributed under the License is distributed on an "AS IS" BASIS,
#   WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
#   See the License for the specific language governing permissions and
#   limitations under the License.


#python imports
import email as email
import email.Header as Header
import email.Message as Message
import email.Utils as emailUtils
from email.MIMEText import MIMEText
from email.MIMENonMultipart import MIMENonMultipart
from email.MIMEMessage import MIMEMessage
from osaf.pim.items import TriageEnum
import logging as logging
import mimetypes
from datetime import datetime
from PyICU import ICUtzinfo

#Chandler imports
import osaf.pim.mail as Mail
from osaf.pim import has_stamp, EventStamp, Remindable
from PyICU import UnicodeString
from i18n import ChandlerMessageFactory as _

#Chandler Mail Service imports
import constants
from utils import *
from utils import Counter
from osaf.pim import TriageEnum

logger = logging.getLogger(__name__)

"""
Performance:
   1. Reduce checks when downloading mail
   2. Remove verbose method calls


Notes:
1. ***Need to pay attention for when setting values in Message.Message object as they must 
   be of type str

XXX: get_param() returns a tuple
XXX: test_email.py, test_email_codecs.py in email package has good unicode examples
XXX: Look at Scrubber.py in Mailman package
XXX: get_filename() unquotes the unicode value

1. Encoding Email Address: Only encode name if present (I have example code)

To Do:
-------
1. Work with Apple Mail and see how it handle display of various message types and copy
2. Look at optimizations for Feedparser to prevent memory hogging (might tie in to twisted dataReceived)
3. Add i18n support to outbound message
4. Look at test_Big5-2 it is not working anymore
5. Add the HTML Cleaner API from Amazon


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

__all__ = ['messageTextToKind', 'messageObjectToKind', 'kindToMessageObject', 'kindToMessageText']

def decodeHeader(header, charset=constants.DEFAULT_CHARSET):
    try:
        decoded    = Header.make_header(Header.decode_header(header))
        unicodeStr = decoded.__unicode__()

        return  constants.EMPTY.join(unicodeStr.splitlines())

    except(UnicodeError, UnicodeDecodeError, LookupError):
        return unicode("".join(header.splitlines()), charset, 'ignore')

def getUnicodeValue(val, charset=constants.DEFAULT_CHARSET):
    assert isinstance(val, str), "The value to convert must be a string"
    assert charset is not None, "A charset must be specified"

    try:
        # The PyICU UnicodeString is used because
        # ICU has support for more character set
        # encodings than Python.
        return unicode(UnicodeString(val, charset))

    except Exception:
        if  charset != constants.DEFAULT_CHARSET:
            return getUnicodeValue(val)

        return constants.EMPTY

def createChandlerHeader(postfix):
    """
    Creates a chandler header with postfix provided.
    """
    assert isinstance(postfix, str), "You must pass A String"

    return constants.CHANDLER_HEADER_PREFIX + postfix

def isChandlerHeader(header):
    """
    Returns true if the header is Chandler defined header.
    """
    assert hasValue(header), "You must pass a String"

    if header.startswith(constants.CHANDLER_HEADER_PREFIX):
        return True

    return False

def populateStaticHeaders(messageObject):
    """
    Populates the static mail headers.
    """
    if not messageObject.has_key('User-Agent'):
        messageObject['User-Agent'] = constants.CHANDLER_USERAGENT

    if not messageObject.has_key('MIME-Version'):
        messageObject['MIME-Version'] = "1.0"


    if not messageObject.has_key('Content-Transfer-Encoding'):
        messageObject['Content-Transfer-Encoding'] = "8bit"


def populateHeader(messageObject, param, var, hType='String', encode=False):
    if hType == 'String':
        if hasValue(var):
            if encode:
                messageObject[param] = Header.Header(var).encode()

            else:
                messageObject[param] = var

    elif(hType == 'EmailAddress'):
        if var is not None and hasValue(var.emailAddress):
            messageObject[param] = Mail.EmailAddress.format(var, encode=True)

def populateHeaders(mailMessage, messageObject):
    keys = mailMessage.headers.keys()

    for key in keys:
        #XXX: Willl need to detect i18n charset and encoded if needed
        messageObject[key] = mailMessage.headers[key]


def populateChandlerHeaders(mailMessage, messageObject):
    keys = mailMessage.chandlerHeaders.keys()

    for key in keys:
        #XXX: Willl need to detect i18n charset and encoded if needed
        messageObject[key] = mailMessage.chandlerHeaders[key]


def populateEmailAddresses(mailMessage, messageObject):
    populateHeader(messageObject, 'From', mailMessage.fromAddress, 'EmailAddress')
    populateHeader(messageObject, 'Reply-To', mailMessage.replyToAddress, 'EmailAddress')

    populateEmailAddressList(mailMessage.toAddress, messageObject, 'To')
    populateEmailAddressList(mailMessage.ccAddress, messageObject, 'Cc')

def populateEmailAddressList(emailAddressList, messageObject, key):
    addrs = []

    for address in emailAddressList:
        if hasValue(address.emailAddress):
            addrs.append(Mail.EmailAddress.format(address, encode=True))

    if len(addrs) > 0:
        messageObject[key] = ", ".join(addrs)


def messageTextToKind(view, messageText, indexText=False, compression='bz2'):
    """
    This method converts a email message string to
    a Chandler C{Mail.MailMessage} object

    @param messageText: A string representation of a mail message
    @type messageText: string
    @return: C{Mail.MailMessage}
    """

    assert isinstance(messageText, str), "messageText must be a String"

    return messageObjectToKind(view, email.message_from_string(messageText),
                               messageText, compression)


def messageObjectToKind(view, messageObject, messageText=None,
                        indexText=False, compression='bz2'):
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
           "messageObject data is not a valid RFC2822 message"

    assert messageText is None or isinstance(messageText, str), \
           "messageText can either be a string or None"

    # Create an item to represent this message.
    # If this message came with an ICS attachment, parse it first; ICalendar
    # will return an item that we can stamp as mail. Otherwise, just create
    # a MailMessage.

    def importIcalendarPayload(mailobj):
        if mailobj.get_content_type() == "text/calendar":
            import osaf.sharing.ICalendar as ICalendar
            try:
                items = ICalendar.itemsFromVObject(view, mailobj.get_payload(),
                                                   filters=(Remindable.reminders.name,))[0]
            except:
                # ignore parts we can't parse [log something?]
                pass
            else:
                if len(items) > 0:
                    # We got something - stamp the first thing as a MailMessage
                    # and use it. (If it was an existing event, we'll reuse it.)
                    m = items[0]
                    if not has_stamp(m, Mail.MailStamp):
                        m = Mail.MailStamp(m)
                        m.add()
                    return m
        return None

    m = importIcalendarPayload(messageObject)
    if m is None and messageObject.is_multipart():
        for mimePart in messageObject.get_payload():
            if mimePart.get_content_type() == "text/calendar":
                m = importIcalendarPayload(mimePart)
                if m is not None:
                    # In case we found an existing event to update,
                    # force its triageStatus to 'now' (bug 6314)
                    m.itsItem.triageStatus = TriageEnum.now
                    break

    if m is None:
        # Didn't find a parsable ICS attachment: just treat it as a mail msg.
        m = Mail.MailMessage(itsView=view)

    """
    Save the original message text in a text blob
    """
    if messageText is None:
        messageText = messageObject.as_string()

    m.rfc2822Message = dataToBinary(m, "rfc2822Message", messageText,
                                    'message/rfc822', compression, False)

    counter = Counter()
    bodyBuffer = []
    buf = None

    if verbose():
        if messageObject.has_key("Message-ID"):
            messageId = messageObject["Message-ID"]
        else:
            messageId = "<Unknown Message>"

        buf = ["Message: %s\n-------------------------------" % messageId]

    __parsePart(view, messageObject, m, bodyBuffer, counter, buf,
                compression=compression)

    """
    If the message has attachments set hasMimeParts to True
    """
    if len(m.mimeParts) > 0:
        m.hasMimeParts = True

    body = constants.LF.join(bodyBuffer).replace(constants.CR, constants.EMPTY)

    # If our private event-description header's there, and we made an event 
    # from this item, remove the header from the start of the body.
    eventDescriptionLength = int(messageObject.get(createChandlerHeader(\
        "EventDescriptionLength"), "0"))
    if eventDescriptionLength and has_stamp(m, Mail.MailStamp):
        body = body[eventDescriptionLength:]

    m.itsItem.body = body

    __parseHeaders(view, messageObject, m)

    if verbose():
        trace("\n\n%s\n\n" % '\n'.join(buf))

    return m

def kindToMessageObject(mailMessage):
    """
    This method converts a email message string to
    a Chandler C{Mail.MailMessage} object

    @param mailMessage: A C{email.Message} object representation of a mail message
    @type mailMessage: C{email.Message}

    @return: C{Message.Message}
    """

    assert has_stamp(mailMessage, Mail.MailStamp), \
           "mailMessage must have been stamped as a Mail.MailStamp"

    messageObject = Message.Message()

    """
    Create a messageId if none exists
    """
    
    stampedMail = Mail.MailStamp(mailMessage)
    if not hasValue(stampedMail.messageId):
        stampedMail.messageId = createMessageID()

    populateHeader(messageObject, 'Message-ID', stampedMail.messageId)
    populateHeader(messageObject, 'Date', stampedMail.dateSentString)
    populateEmailAddresses(stampedMail, messageObject)
    populateStaticHeaders(messageObject)
    populateChandlerHeaders(stampedMail, messageObject)
    populateHeaders(stampedMail, messageObject)
    populateHeader(messageObject, 'Subject', stampedMail.about, encode=True)

    if getattr(mailMessage, "inReplyTo", None):
        populateHeader(messageObject, 'In-Reply-To', mailMessage.inReplyTo, encode=False)

    if mailMessage.referencesMID and len(mailMessage.referencesMID):
        messageObject["References"] = " ".join(mailMessage.referencesMID)

    try:
        payload = mailMessage.body
    except AttributeError:
        payload = u""

    event = EventStamp(mailMessage)
    hasAttachments =  mailMessage.getNumberOfAttachments() > 0

    try:
        timeDescription = event.getTimeDescription()
        hasICal = True
    except AttributeError:
        hasICal = False

    if not hasICal and not hasAttachments:
        #There are no attachments or Ical events so just add the
        #body text as the payload and return the messageObject
        messageObject['Content-Type'] = "text/plain; charset=utf-8; format=flowed"
        messageObject.set_payload(payload.encode("utf-8"))
        return messageObject

    messageObject.set_type("multipart/mixed")

    if hasICal:
         # If this message is an event, prepend the event description to the body,
         # and add the event data as an attachment.
         # @@@ This probably isn't the right place to do this (since it couples the
         # email service to events and ICalendarness), but until we resolve the architectural
         # questions around stamping, it's good enough.

        # It's an event - prepend the description to the body, make the
        # message multipart, and add the body & ICS event as parts. Also,
        # add a private header telling us how long the description is, so
        # we'll know what to remove on the receiving end.
        # @@@ I tried multipart/alternative here, but this hides the attachment
        # completely on some clients...
        # @@@ In formatting the prepended description, I'm adding an extra newline
        # at the end so that Apple Mail will display the .ics attachment on its own line.
        location = unicode(getattr(event, 'location', u''))
        if len(location.strip()) > 0:
            evtDesc =  _(u"When: %(whenValue)s\nWhere: %(locationValue)s") \
                       % { 'whenValue': timeDescription,
                           'locationValue': location
                         }
        else:
            evtDesc =  _(u"When: %(whenValue)s") \
                       % { 'whenValue': timeDescription }

        payload = _(u"%(eventDescription)s\n\n%(bodyText)s\n") \
                   % {'eventDescription': evtDesc,
                      'bodyText': payload
                     }

        messageObject.attach(MIMEText(payload.encode('utf-8'), _charset='utf-8'))
        messageObject.add_header(createChandlerHeader("EventDescriptionLength"),
                                 str(len(evtDesc)))

        # Format this message as an ICalendar object
        import osaf.sharing.ICalendar as ICalendar
        calendar = ICalendar.itemsToVObject(mailMessage.itsItem.itsView,
                        [event], filters=(Remindable.reminders.name,))
        calendar.add('method').value="REQUEST"
        ics = calendar.serialize().encode('utf-8')

        # Attach the ICalendar object
        icsPayload = MIMENonMultipart('text', 'calendar',
                                      method='REQUEST', charset='utf-8')

        fname = Header.Header(_(u"event.ics")).encode()
        icsPayload.add_header("Content-Disposition", "attachment", filename=fname)
        icsPayload.set_payload(ics)
        messageObject.attach(icsPayload)
    else:
        messageObject.attach(MIMEText(payload.encode('utf-8'), _charset='utf-8'))

    if hasAttachments:
        #add the attachents to multipart container

        attachments = mailMessage.getAttachments()

        for attachment in attachments:
            if has_stamp(attachment, Mail.MailStamp):
                try:
                    rfc2822 = binaryToData(Mail.MailStamp(attachment).rfc2822Message)
                except AttributeError:
                    rfc2822 = kindToMessageText(attachment, False)

                message = email.message_from_string(rfc2822)
                rfc2822Payload = MIMEMessage(message)
                messageObject.attach(rfc2822Payload)

    return messageObject


def kindToMessageText(mailMessage, saveMessage=True):
    """
    This method converts a email message string to
    a Chandler C{Mail.MailMessage} object

    @param mailMessage: A C{email.Message} object representation of a mail message
    @type mailMessage: C{email.Message}
    @param saveMessage: save the message text converted from the C{email.Message}
                        in the mailMessage.rfc2822Message attribute
    @type saveMessage: C{Boolean}
    @return: C{str}
    """

    assert has_stamp(mailMessage, Mail.MailStamp), \
           "mailMessage must have been stamped as a Mail.MailStamp"

    try:
        messageObject = kindToMessageObject(mailMessage)
    except Exception, e:
        logger.debug(e)
        raise
    messageText = messageObject.as_string()

    if saveMessage:
        mailMessage.rfc2822Message = dataToBinary(mailMessage, "rfc2822Message",
                                           messageText, 'message/rfc822', 'bz2')

    return messageText


def __parseHeaders(view, messageObject, m):

    date = messageObject['Date']

    if date is not None:
        parsed = emailUtils.parsedate_tz(date)

        """
        It is a non-rfc date string
        """
        if parsed is None:
            if __debug__:
                trace("Message contains a Non-RFC Compliant Date format")

            """
            Set the sent date to the current Date
            """
            m.dateSent = datetime.now(ICUtzinfo.default)

        else:
            m.dateSent = datetime.fromtimestamp(emailUtils.mktime_tz(parsed),
                                                ICUtzinfo.default)

        ##XXX:  Do we need this the tz could be preserved
        m.dateSentString = date
        del messageObject['Date']

    else:
        m.dateSent = getEmptyDate()
        m.dateSentString = ""

    if messageObject['References']:
        refList = messageObject['References'].split()

        for ref in refList:
            ref = ref.strip()
            if ref:
                m.referencesMID.append(ref)

        del messageObject['References']

    __assignToKind(view, m, messageObject, 'Subject', 'String', 'subject')
    __assignToKind(view, m, messageObject, 'In-Reply-To', 'String', 'inReplyTo')
    __assignToKind(view, m, messageObject, 'From', 'EmailAddress', 'fromAddress')
    __assignToKind(view, m, messageObject, 'Reply-To', 'EmailAddress', 'replyToAddress')
    __assignToKind(view, m.toAddress, messageObject, 'To', 'EmailAddressList')
    __assignToKind(view, m.ccAddress, messageObject, 'Cc', 'EmailAddressList')
    __assignToKind(view, m.bccAddress, messageObject, 'Bcc', 'EmailAddressList')

    """
    Do not decode the message ID as it requires no i18n processing
    """
    __assignToKind(view, m, messageObject, 'Message-ID', 'String', 'messageId', False, False)

    m.chandlerHeaders = {}
    m.headers = {}

    #XXX: Will want to selectively decodeHeaders for i18n support see RFC: 2231 
    #     for more info

    for (key, val) in messageObject.items():
        if isChandlerHeader(key):
            m.chandlerHeaders[getUnicodeValue(key)] = getUnicodeValue(val)

        else:
            m.headers[getUnicodeValue(key)] = getUnicodeValue(val)

        del messageObject[key]

def __assignToKind(view, kindVar, messageObject, key, hType, attr=None, decode=True, makeUnicode=True):
    header = messageObject.get(key)

    if header is None:
        return

    if decode:
        header = decodeHeader(header)
    elif makeUnicode:
        header = getUnicodeValue(header)

    if hType == "String":
        setattr(kindVar, attr, header)

    # XXX: This logic will need to be expanded
    elif hType == "StringList":
        kindVar.append(header)

    elif hType == "EmailAddress":
        name, addr = emailUtils.parseaddr(messageObject.get(key))

        ea = __getEmailAddress(view, decodeHeader(name), getUnicodeValue(addr))

        if ea is not None:
            setattr(kindVar, attr, ea)

        elif __debug__:
            trace("__assignToKind: invalid email address found %s: %s" % (key, addr))

    elif hType == "EmailAddressList":
        for name, addr in emailUtils.getaddresses(messageObject.get_all(key, [])):
            ea = __getEmailAddress(view, decodeHeader(name), getUnicodeValue(addr))

            if ea is not None:
                kindVar.append(ea)

            elif __debug__:
                trace("__assignToKind: invalid email address found %s: %s" % (key, addr))

    del messageObject[key]


def __getEmailAddress(view, name, addr):
    """
    Use any existing EmailAddress, but don't update them
    because that will cause the item to go stale in the UI thread.
    """
    #XXX: This method needs much better performance
    #return Mail.EmailAddress.getEmailAddress(view, addr, name, True)

    if Mail.EmailAddress.isValidEmailAddress(addr):
        address = Mail.EmailAddress.findEmailAddress(view, addr)
        if address is None:
            address = Mail.EmailAddress(itsView=view,
                                        emailAddress=addr, fullName=name)
    else:
        address = None

    return address


def __parsePart(view, mimePart, parentMIMEContainer, bodyBuffer, counter, buf,
                level=0, compression='bz2'):
    __checkForDefects(mimePart)

    if isinstance(mimePart, str):
        #XXX: The mimePart value on bad messages will be individual characters of a message body.
        #     This is coming from the Python email package but I believe it is a bug.
        #     need to investigate further!
        bodyBuffer.append(getUnicodeValue(mimePart))
        return

    maintype  = mimePart.get_content_maintype()

    if maintype == "message":
        __handleMessage(view, mimePart, parentMIMEContainer, bodyBuffer,
                        counter, buf, level, compression)

    elif maintype == "multipart":
        __handleMultipart(view, mimePart, parentMIMEContainer, bodyBuffer,
                          counter, buf, level, compression)

    elif maintype == "text":
        __handleText(view, mimePart, parentMIMEContainer, bodyBuffer,
                     counter, buf, level, compression)

    else:
        __handleBinary(view, mimePart, parentMIMEContainer,
                       counter, buf, level, compression)


def __handleMessage(view, mimePart, parentMIMEContainer, bodyBuffer,
                    counter, buf, level, compression):
    subtype   = mimePart.get_content_subtype()
    multipart = mimePart.is_multipart()

    if verbose():
        __trace("message/%s" % subtype, buf, level)

    """
    If the message is multipart then pass decode=False to
    get_poyload otherwise pass True.
    """
    payload = mimePart.get_payload(decode=not multipart)
    assert payload is not None, "__handleMessage payload is None"

    if subtype == "rfc822":
        if multipart:
            sub = mimePart.get_payload()[0]
            assert sub is not None, "__handleMessage sub is None"

            tmp = [u'\n']

            __appendHeader(sub, tmp, "From")
            __appendHeader(sub, tmp, "Reply-To")
            __appendHeader(sub, tmp, "Date")
            __appendHeader(sub, tmp, "To")
            __appendHeader(sub, tmp, "Cc")
            __appendHeader(sub, tmp, "Subject")

            tmp.append(u'\n')

            bodyBuffer.append(constants.LF.join(tmp))

        elif __debug__:
            trace("******WARNING****** message/rfc822 part not Multipart investigate")

    elif subtype == "delivery-status":
        """
        Add the delivery status info to the message body
        """
        bodyBuffer.append(getUnicodeValue(mimePart.as_string()))
        return

    elif subtype == "disposition-notification-to":
        """
        Add the disposition-notification-to info to the message body
        """
        bodyBuffer.append(getUnicodeValue(mimePart.as_string()))
        return

    elif subtype == "external-body":
        if __debug__:
            trace("Chandler Mail Service does not support message/external-body at this time")
        return

    elif subtype == "http":
        if __debug__:
            trace("Chandler Mail Service does not support message/http at this time")
        return

    elif subtype == "partial":
        if __debug__:
            trace("Chandler Mail Service does not support message/partial at this time")
        return

    if multipart:
        for part in payload:
            __parsePart(view, part, parentMIMEContainer, bodyBuffer,
                        counter, buf, level+1, compression)

    elif __debug__:
        trace("******WARNING****** message/%s payload not multipart" % subtype)


def __handleMultipart(view, mimePart, parentMIMEContainer, bodyBuffer,
                      counter, buf, level, compression):
    subtype   = mimePart.get_content_subtype()
    multipart = mimePart.is_multipart()

    if verbose():
        __trace("multipart/%s" % subtype, buf, level)

    """
    If the message is multipart then pass decode=False to
    get_poyload otherwise pass True
    """
    payload = mimePart.get_payload(decode=not multipart)
    assert payload is not None, "__handleMultipart payload is None"

    if subtype == "alternative":
        """
        An alternative container should always have at least one part
        """
        if len(payload) > 0:
            foundText = False
            firstPart = None

            for part in payload:
                if part.get_content_type() == "text/plain":
                    __handleText(view, part, parentMIMEContainer, bodyBuffer,
                                 counter, buf, level+1, compression)
                    foundText = True

                elif firstPart is None and not foundText and not part.is_multipart():
                    """
                    A multipart/alternative container should have
                    at least one part that is not multipart and
                    is text based (plain, html, rtf) for display
                    """
                    firstPart = part

                elif part.is_multipart():
                    """
                    If we find a multipart sub-part with in the alternative part handle
                    it
                    """
                    __handleMultipart(view, part, parentMIMEContainer, bodyBuffer, \
                                      counter, buf, level+1, compression)

            if not foundText and firstPart is not None:
                if firstPart.get_content_maintype() == "text":
                    __handleText(view, firstPart, parentMIMEContainer,
                                 bodyBuffer, counter, buf, level+1, compression)
                else:
                    __handleBinary(view, firstPart, parentMIMEContainer, counter, buf, level+1, compression)
        elif __debug__:
            trace("******WARNING****** multipart/alternative has no payload")

    elif subtype == "byteranges":
        if __debug__:
            trace("Chandler Mail Service does not support multipart/byteranges at this time")
        return

    elif subtype == "form-data":
        if __debug__:
            trace("Chandler Mail Service does not support multipart/form-data at this time")
        return

    else:
        if subtype == "signed":
            if __debug__:
                trace("Chandler Mail Service does not validate multipart/signed at this time")

        elif subtype == "encrypted":
            if __debug__:
                trace("Chandler Mail Service does not validate multipart/encrypted at this time")

        for part in payload:
            __parsePart(view, part, parentMIMEContainer, bodyBuffer,
                        counter, buf, level+1, compression)


def __handleBinary(view, mimePart, parentMIMEContainer,
                   counter, buf, level, compression):
    contype = mimePart.get_content_type()

    if verbose():
        __trace(contype, buf, level)

    """
    skip AppleDouble resource files per RFC1740
    """
    if contype == "application/applefile":
        return

    mimeBinary = Mail.MIMEBinary(itsView=view)

    """
    Get the attachments data
    """
    data = mimePart.get_payload(decode=1)
    assert data is not None, "__handleBinary data is None"

    mimeBinary.filesize = len(data)
    mimeBinary.filename = __getFileName(mimePart, counter)
    mimeBinary.mimeType = contype

    """
    Try to figure out what the real mimetype is
    """
    if contype == "application/octet-stream" and \
        not mimeBinary.filename.endswith(".bin"):
        result = mimetypes.guess_type(mimeBinary.filename, strict=False)

        if result[0] is not None:
            mimeBinary.mimeType = result[0]

    mimeBinary.data = dataToBinary(mimeBinary, "data", data,
                                   mimeBinary.mimeType, compression)

    parentMIMEContainer.mimeParts.append(mimeBinary.itsItem)

def __handleText(view, mimePart, parentMIMEContainer, bodyBuffer,
                 counter, buf, level, compression):
    subtype = mimePart.get_content_subtype()

    if verbose():
        __trace("text/%s" % subtype, buf, level)

    """
    Get the attachment data
    """
    body = mimePart.get_payload(decode=1)

    size = len(body)

    charset = mimePart.get_content_charset(constants.DEFAULT_CHARSET)
    lang    = mimePart.get("Content-language")

    if subtype == "plain" or subtype == "rfc822-headers":
        #XXX: Will want to leverage the language to aid the GUI layer
        size > 0 and bodyBuffer.append(getUnicodeValue(body, charset))

    else:
        mimeText = Mail.MIMEText(itsView=view)

        mimeText.mimeType = mimePart.get_content_type()
        mimeText.charset  = charset
        mimeText.filesize = len(body)
        mimeText.filename = __getFileName(mimePart, counter)

        if lang:
            mimeText.lang = lang

        mimeText.itsItem.body = getUnicodeValue(body, charset)

        parentMIMEContainer.mimeParts.append(mimeText.itsItem)
        parentMIMEContainer.hasMimeParts = True

def __getFileName(mimePart, counter):
    #This can return none, a str, or unicode :(
    filename = mimePart.get_filename()

    if filename:
        if isinstance(filename, str):
            return getUnicodeValue(filename)
        return filename

    """
    No Filename need to create an arbitrary name
    """
    ext = mimetypes.guess_extension(mimePart.get_content_type())

    if not ext:
        ext = '.bin'

    return u'Attachment-%s%s' % (counter.nextValue(), ext)

def __checkForDefects(mimePart):
    if __debug__ and len(mimePart.defects) > 0:
        strBuffer = [mimePart.get("Message-ID", "Unknown Message ID")]
        handled = False

        for defect in mimePart.defects:
            """
            Just get the class name strip the package path
            """
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

        trace("*****WARNING**** Mail Parsing defect: %s" % ", ".join(strBuffer))

def __appendHeader(mimePart, buf, header):
    if mimePart.has_key(header):
        buf.append(u"%s: %s" % (getUnicodeValue(header), decodeHeader(mimePart[header])))

def verbose():
    return __debug__ and constants.VERBOSE

def __trace(contype, buf, level):
    buf.append("%s %s" % (level * "  ", contype))
