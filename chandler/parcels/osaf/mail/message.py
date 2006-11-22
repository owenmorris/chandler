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
from i18n import ChandlerMessageFactory as _

#Chandler Mail Service imports
import constants
from constants import IGNORE_ATTACHMENTS
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

To Do:
-------
1. Work with Apple Mail and see how it handle display of various message types and copy
2. Look at optimizations for Feedparser to prevent memory hogging (might tie in to twisted dataReceived)
3. Look at test_Big5-2 it is not working anymore
"""

__all__ = ['messageTextToKind', 'messageObjectToKind', 'kindToMessageObject', 'kindToMessageText']

def decodeHeader(header, charset=constants.DEFAULT_CHARSET):
    try:
        h = Header.decode_header(header)
        buf = [b[0].decode(b[1] or 'ascii') for b in h]
        return u''.join(buf)

    except(UnicodeError, UnicodeDecodeError, LookupError):
        return unicode("".join(header.splitlines()), charset, 'ignore')

def getUnicodeValue(val, charset=constants.DEFAULT_CHARSET, ignore=False):
    assert isinstance(val, str), "The value to convert must be a string"
    assert charset is not None, "A charset must be specified"

    try:
        if ignore:
            return unicode(val, charset, 'ignore')

        return unicode(val, charset)

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
        messageObject[key] = mailMessage.headers[key]


def populateChandlerHeaders(mailMessage, messageObject):
    keys = mailMessage.chandlerHeaders.keys()

    for key in keys:
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

    #XXX Performance and memory use are issues with the Python email package
    #    look for ways to improve
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

    #XXX The ics file should be removed from the email and not
    # saved as a attachment on MailStamp

    def importIcalendarPayload(messageObject):
        if messageObject.get_content_type() == "text/calendar":
            import osaf.sharing.ICalendar as ICalendar
            try:
                items = ICalendar.itemsFromVObject(view, messageObject.get_payload(),
                                                   filters=(Remindable.reminders.name,))[0]
            except:
                # ignore parts we can't parse [log something?]
                pass
            else:
                if len(items) > 0:
                    # We got something - stamp the first thing as a MailMessage
                    # and use it. (If it was an existing event, we'll reuse it.)
                    eventStamp = items[0]
                    item = eventStamp.itsItem

                    if not has_stamp(item, Mail.MailStamp):
                        mailStamp = Mail.MailStamp(item)
                        mailStamp.add()
                    else:
                        mailStamp = Mail.MailStamp(item)

                    return mailStamp
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

    if not IGNORE_ATTACHMENTS:
        """
        Save the original message text in a text blob
        """
        if messageText is None:
            messageText = messageObject.as_string()

        m.rfc2822Message = dataToBinary(m, "rfc2822Message", messageText,
                                        'message/rfc822', compression, False)

    counter = Counter()
    bodyBuffer = {'plain': [], 'html': []}
    buf = None

    if verbose():
        if messageObject.has_key("Message-ID"):
            messageId = messageObject["Message-ID"]
        else:
            messageId = "<Unknown Message>"

        buf = ["Message: %s\n-------------------------------" % messageId]

    __parsePart(view, messageObject, m, bodyBuffer, counter, buf,
                compression=compression)

    if len(bodyBuffer.get('plain')):
        body = constants.LF.join(bodyBuffer.get('plain')).replace(constants.CR, constants.EMPTY)

    elif len(bodyBuffer.get('html')):
        htmlBuffer = bodyBuffer.get('html')

        for i in xrange(0, len(htmlBuffer)):
            htmlBuffer[i] = stripHTML(htmlBuffer[i])

        body = constants.LF.join(htmlBuffer).replace(constants.CR, constants.EMPTY)

    else:
        #No plain text or html mime types in the mail message
        body = u""

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
    stampedMail = Mail.MailStamp(mailMessage)

    """
    Create a messageId if none exists
    """

    if not hasValue(stampedMail.messageId):
        stampedMail.messageId = createMessageID()

    populateHeader(messageObject, 'Message-ID', stampedMail.messageId)
    populateHeader(messageObject, 'Date', stampedMail.dateSentString)
    populateEmailAddresses(stampedMail, messageObject)
    populateStaticHeaders(messageObject)
    populateChandlerHeaders(stampedMail, messageObject)
    populateHeaders(stampedMail, messageObject)
    populateHeader(messageObject, 'Subject', stampedMail.subject, encode=True)

    if getattr(stampedMail, "inReplyTo", None):
        populateHeader(messageObject, 'In-Reply-To', stampedMail.inReplyTo, encode=False)

    if stampedMail.referencesMID and len(stampedMail.referencesMID):
        messageObject["References"] = " ".join(stampedMail.referencesMID)

    try:
        payload = mailMessage.body
    except AttributeError:
        payload = u""

    event = EventStamp(mailMessage)
    hasAttachments =  stampedMail.getNumberOfAttachments() > 0

    try:
        timeDescription = event.getTimeDescription()
        isEvent = True
    except AttributeError:
        isEvent = False

    if not isEvent and not hasAttachments:
        #There are no attachments or Ical events so just add the
        #body text as the payload and return the messageObject
        messageObject.set_payload(payload.encode("utf-8"), charset="utf-8")
        return messageObject

    messageObject.set_type("multipart/mixed")

    if isEvent:
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

        mt = MIMEText(payload.encode('utf-8'), _charset="utf-8")
        messageObject.attach(mt)
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
                                      method='REQUEST', _charset="utf-8")

        fname = Header.Header(_(u"event.ics")).encode()
        icsPayload.add_header("Content-Disposition", "attachment", filename=fname)
        icsPayload.set_payload(ics)
        messageObject.attach(icsPayload)
    else:
        mt = MIMEText(payload.encode('utf-8'), _charset="utf-8")
        messageObject.attach(mt)

    if hasAttachments:
        attachments = stampedMail.getAttachments()

        for attachment in attachments:
            if has_stamp(attachment, Mail.MailStamp):
                # The attachment is another MailMessage
                try:
                    rfc2822 = binaryToData(Mail.MailStamp(attachment).rfc2822Message)
                except AttributeError:
                    rfc2822 = kindToMessageText(attachment, False)

                message = email.message_from_string(rfc2822)
                rfc2822Payload = MIMEMessage(message)
                messageObject.attach(rfc2822Payload)

            else:
                m = Mail.MIMEText(attachment)

                if m.mimeType == u"text/calendar":
                    icsPayload = MIMENonMultipart('text', 'calendar', \
                                        method='REQUEST', _charset="utf-8")

                    fname = Header.Header(m.filename).encode()
                    icsPayload.add_header("Content-Disposition", "attachment", filename=fname)
                    icsPayload.set_payload(m.data.encode('utf-8'))
                    messageObject.attach(icsPayload)

    return messageObject


def kindToMessageText(mailMessage, saveMessage=False):
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
        mailStamp = Mail.MailStamp(mailMessage)
        mailStamp.rfc2822Message = dataToBinary(mailMessage, "rfc2822Message",
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
            try:
                m.dateSent = datetime.fromtimestamp(emailUtils.mktime_tz(parsed),
                                                    ICUtzinfo.default)
            except:
                m.dateSent = datetime.now(ICUtzinfo.default)

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

    address = None

    if Mail.EmailAddress.isValidEmailAddress(addr):
        address = Mail.EmailAddress.findEmailAddress(view, addr)

    if address is None:
        address = Mail.EmailAddress(itsView=view,
                                    emailAddress=addr, fullName=name)
    return address


def __parsePart(view, mimePart, parentMIMEContainer, bodyBuffer, counter, buf,
                level=0, compression='bz2'):

    __checkForDefects(mimePart)

    if isinstance(mimePart, str):
        #XXX: The mimePart value on bad messages will be individual characters of a message body.
        #     This is coming from the Python email package but I believe it is a bug.
        #     need to investigate further!
        bodyBuffer.get('plain').append(getUnicodeValue(mimePart))
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

            bodyBuffer.get('plain').append(constants.LF.join(tmp))

        elif __debug__:
            trace("******WARNING****** message/rfc822 part not Multipart investigate")

    elif subtype == "delivery-status":
        """
        Add the delivery status info to the message body
        """
        bodyBuffer.get('plain').append(getUnicodeValue(mimePart.as_string()))
        return

    elif subtype == "disposition-notification-to":
        """
        Add the disposition-notification-to info to the message body
        """
        bodyBuffer.get('plain').append(getUnicodeValue(mimePart.as_string()))
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

    if IGNORE_ATTACHMENTS:
        return

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

    if size and (subtype == "plain" or subtype == "rfc822-headers"):
        bodyBuffer.get('plain').append(getUnicodeValue(body, charset,ignore=True))

    else:
        if size and subtype == "html" and len(bodyBuffer.get('plain')) == 0:
            bodyBuffer.get('html').append(getUnicodeValue(body, charset, ignore=True))

        if IGNORE_ATTACHMENTS:
            return

        mimeText = Mail.MIMEText(itsView=view)
        mimeText.mimeType = mimePart.get_content_type()
        mimeText.charset  = charset
        mimeText.filesize = len(body)
        mimeText.filename = __getFileName(mimePart, counter)

        lang = mimePart.get("Content-language")

        if lang:
            mimeText.lang = lang

        mimeText.itsItem.body = getUnicodeValue(body, charset)

        parentMIMEContainer.mimeParts.append(mimeText.itsItem)

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
