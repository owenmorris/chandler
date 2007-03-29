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
import email
from email import Header, Message
import email.Utils as emailUtils
from email.MIMENonMultipart import MIMENonMultipart
from email.MIMEMessage import MIMEMessage
import logging as logging
import mimetypes
from datetime import datetime
from PyICU import ICUtzinfo

#Chandler imports
from osaf.pim.mail import EmailAddress, MailMessage, MIMEText, MIMEBinary, getMessageBody, getCurrentMeEmailAddresses
from osaf.pim.calendar.Calendar import parseText, setEventDateTime
from osaf.pim import has_stamp, TaskStamp, EventStamp, MailStamp, Remindable
from i18n import ChandlerMessageFactory as _
#from i18n import getLocale
from osaf.sharing import (getFilter, errors as sharingErrors, SharedItem, inbound, outbound)
from application import schema

#Chandler Mail Service imports
import constants
from constants import IGNORE_ATTACHMENTS
from utils import *
from utils import Counter

"""
Performance:
   1. Reduce checks when downloading mail

Notes:
1. ***Need to pay attention for when setting values in Message.Message object as they must 
   be of type str

XXX: get_param() returns a tuple
XXX: test_email.py, test_email_codecs.py in email package has good unicode examples
XXX: Look at Scrubber.py in Mailman package
XXX: get_filename() unquotes the unicode value

To Do:
-------
1. Look at optimizations for Feedparser to prevent memory hogging (might tie in to twisted dataReceived)
2. Look at test_Big5-2 it is not working anymore
"""

__all__ = ['messageTextToKind', 'kindToMessageText', 'parseEventInfo', 'parseTaskInfo']


OUTBOUND_FILTERS = getFilter(['cid:triage-filter@osaf.us', 'cid:event-status-filter@osaf.us',
                              'cid:reminders-filter@osaf.us', 'cid:bcc-filter@osaf.us',
                              'cid:dateSent-filter@osaf.us', 'cid:headers-filter@osaf.us',
                              'cid:inReplyTo-filter@osaf.us', 'cid:references-filter@osaf.us',
                              'cid:messageId-filter@osaf.us',])



class MIMEBase64Encode(MIMENonMultipart):
    def __init__(self, _data, _maintype='text', _subtype='plain',
                _charset='utf-8', **_params):

        if _maintype is None:
            raise TypeError('Invalid application MIME maintype')

        if _subtype is None:
            raise TypeError('Invalid application MIME subtype')

        MIMENonMultipart.__init__(self, _maintype, _subtype, **_params)

        # Base64 encoded data must first comply with RFC 822
        # CRLF requirement. So make sure CRLF newlines are present
        # before encoding the data
        _data = addCarriageReturn(_data)

        self.set_payload(_data, _charset)



def decodeHeader(header, charset="utf-8"):
    try:
        h = Header.decode_header(header)
        buf = [b[0].decode(b[1] or 'ascii') for b in h]
        return u''.join(buf)

    except(UnicodeError, UnicodeDecodeError, LookupError):
        return unicode("".join(header.splitlines()), charset, 'ignore')

def getUnicodeValue(val, charset="utf-8", ignore=False):
    assert isinstance(val, str), "The value to convert must be a string"
    assert charset is not None, "A charset must be specified"

    try:
        if ignore:
            return unicode(val, charset, 'ignore')

        return unicode(val, charset)

    except Exception:
        if  charset != "utf-8":
            return getUnicodeValue(val)

        return u""

def createChandlerHeader(postfix):
    """
    Creates a chandler header with postfix provided.
    """
    assert isinstance(postfix, str), "You must pass A String"

    return constants.CHANDLER_HEADER_PREFIX + postfix

def populateStaticHeaders(messageObject):
    """
    Populates the static mail headers.
    """

    # Add the Chandler header to outgoing messages
    # This is used to identify which messages on
    # the IMAP or POP server were sent from a
    # Chandler client
    ch = createChandlerHeader("Mailer")

    if not messageObject.has_key(ch):
        messageObject[ch] = 'True'

    if not messageObject.has_key('User-Agent'):
        messageObject['User-Agent'] = constants.CHANDLER_USERAGENT

    if not messageObject.has_key('MIME-Version'):
        messageObject['MIME-Version'] = "1.0"


    if not messageObject.has_key('Content-Transfer-Encoding'):
        messageObject['Content-Transfer-Encoding'] = "7bit"


def populateHeader(messageObject, param, var, hType='String', encode=False):
    if hType == 'String':
        if hasValue(var):
            if encode:
                messageObject[param] = Header.Header(var).encode()

            else:
                messageObject[param] = var

    elif(hType == 'EmailAddress'):
        if var is not None and hasValue(var.emailAddress):
            messageObject[param] =var.format(encode=True)

def populateHeaders(mailMessage, messageObject):
    keys = mailMessage.headers.keys()

    for key in keys:
        messageObject[key] = mailMessage.headers[key]

def populateEmailAddresses(mailMessage, messageObject):
    populateHeader(messageObject, 'From', mailMessage.fromAddress, 'EmailAddress')
    populateHeader(messageObject, 'Reply-To', mailMessage.replyToAddress, 'EmailAddress')

    populateEmailAddressList(mailMessage.toAddress, messageObject, 'To')
    populateEmailAddressList(mailMessage.ccAddress, messageObject, 'Cc')

    originators = mailMessage.getUniqueOriginators()

    if originators:
        populateEmailAddressList(originators, messageObject, 'Cc', append=True)


def populateEmailAddressList(emailAddressList, messageObject, key, append=False):
    addrs = []

    for address in emailAddressList:
        if hasValue(address.emailAddress):
            addrs.append(address.format(encode=True))

    if len(addrs) > 0:
        if append and messageObject.has_key(key) and \
           len(messageObject[key].strip()):
            messageObject[key] += ", %s" % ", ".join(addrs)

        else:
            messageObject[key] = ", ".join(addrs)


def messageTextToKind(view, messageText, indexText=False, compression='bz2'):
    """
    This method converts a email message string to
    a Chandler C{MailMessage} object

    @param messageText: A string representation of a mail message
    @type messageText: string
    @return: C{MailMessage}
    """

    assert isinstance(messageText, str), "messageText must be a String"

    #XXX Performance and memory use are issues with the Python email package
    #    look for ways to improve
    return _messageObjectToKind(view, email.message_from_string(messageText),
                                messageText, compression)


def _messageObjectToKind(view, messageObject, messageText=None,
                        indexText=False, compression='bz2'):
    """
    This method converts a email message string to
    a Chandler C{MailMessage} object

    @param messageObject: A C{email.Message} object representation of a mail message
    @type messageObject: C{email.Message}
    @return: C{MailMessage}
    """

    assert isinstance(messageObject, Message.Message), \
           "messageObject must be a Python email.Message.Message instance"

    assert len(messageObject.keys()) > 0, \
           "messageObject data is not a valid RFC2822 message"

    assert messageText is None or isinstance(messageText, str), \
           "messageText can either be a string or None"

    mailStamp = None
    icsSummary = None
    icsDesc = None

    #XXX issue to deal with later is what happens
    # if more than one ics or eimml attachment in
    # the message
    chAttachments = getChandlerAttachments(messageObject)

    if chAttachments["eimml"]:
        eimml = chAttachments["eimml"][0]

        # Get the from address ie. Sender.
        emailAddr = messageObject.get("From")

        if not emailAddr:
            # A peer address is required for eimml
            # deserialization. If there is no peer
            # then ignore the eimml data.
            return None

        name, addr = emailUtils.parseaddr(emailAddr)

        peer = __getEmailAddress(view, decodeHeader(name), getUnicodeValue(addr))

        if peer in getCurrentMeEmailAddresses(view):
            # If the Chandler EIMML message is from me then
            # ignore it.
            return None

        #used for debugging
        #print (u"inbound: %s uuid: %s" % (peer.format(),  peer.itsUUID)).encode("utf8")

        try:
            item = inbound(peer, removeCarriageReturn(eimml)) #, debug=True)

            mailStamp = MailStamp(item)
            mailStamp.fromEIMML = True

            #used for debugging
            #shared = SharedItem(item)
            #for conflict in shared.getConflicts():
            #    print (u"Conflict found %s: %s" % (conflict.field, conflict.value)).encode("utf8")

        except sharingErrors.MalformedData, e:
            # The eimml records contained bogus
            # syntax and will not be processed
            # Raising an error here would result
            # in the entire mail download being
            # terminated so we log the error
            # instead
            if __debug__:
                logging.exception(e)
            return None

        except sharingErrors.OutOfSequence, e1:
            # The eimml records are older then
            # the current state and are not going
            # to be applied so return None
            if __debug__:
                logging.exception(e1)
            return None

        except Exception, e2:
            # There was an error at the XML parsing layer.
            # Log the error and continue to download.
            if __debug__:
                logging.exception(e2)
            return None

    elif chAttachments["ics"]:
        # if there was a eimml attachment then
        # ignore any ics attachments

        import osaf.sharing.ICalendar as ICalendar

        ics = chAttachments["ics"][0]

        try:
            items = ICalendar.itemsFromVObject(view, removeCarriageReturn(ics),
                                               filters=(Remindable.reminders.name,))[0]
        except Exception, e:
            logging.exception(e)
        else:
            if len(items) > 0:
                # We got something - stamp the first thing as a MailMessage
                # and use it. (If it was an existing event, we'll reuse it.)

                item = items[0]

                if item.displayName and len(item.displayName.strip()):
                    # The displayName will contain the ics summary
                    icsSummary = item.displayName

                if item.body and len(item.displayName.strip()):
                    # The body will contain the ics description
                    icsDesc = item.body

                if not has_stamp(item, MailStamp):
                    if has_stamp(item, EventStamp):
                        EventStamp(item).addStampToAll(MailStamp)
                    else:
                        MailStamp(item)
                        item.add()

                mailStamp = MailStamp(item)

                mailStamp.fromEIMML = False

    if not mailStamp:
        mailStamp = MailMessage(itsView=view)
        mailStamp.fromEIMML = False

    if getattr(mailStamp, "messageId", None):
        # The presence a messageId indicated that
        # this message has already been sent or
        # received and thus has been updated.
        mailStamp.isUpdated = True

    if not IGNORE_ATTACHMENTS:
        # Save the original message text in a text blob
        if messageText is None:
            messageText = messageObject.as_string()

        mailStamp.rfc2822Message = dataToBinary(mailStamp, "rfc2822Message", messageText,
                                               'message/rfc822', compression, False)


    #if verbose():
    #    if messageObject.has_key("Message-ID"):
    #        messageId = messageObject["Message-ID"]
    #    else:
    #        messageId = "<Unknown Message>"
    #
    #    buf = ["Message: %s\n-------------------------------" % messageId]

    if not mailStamp.fromEIMML:
        # Do not parse the message to build the
        # item.body since that data is in the eimml.

        counter = Counter()
        bodyBuffer = {'plain': [], 'html': []}
        buf = None

        # The body of the message will be contained in the eimml so
        # do not try and parse the mail message body.
        __parsePart(view, messageObject, mailStamp, bodyBuffer, counter, buf,
                    compression=compression)

        if len(bodyBuffer.get('plain')):
            body = removeCarriageReturn(u"\n".join(bodyBuffer.get('plain')))

        elif len(bodyBuffer.get('html')):
            htmlBuffer = bodyBuffer.get('html')

            for i in xrange(0, len(htmlBuffer)):
                htmlBuffer[i] = stripHTML(htmlBuffer[i])

            body = removeCarriageReturn(u"\n".join(htmlBuffer))

        else:
            #No plain text or html mime types in the mail message
            body = u""

        mailStamp.body = body

    __parseHeaders(view, messageObject, mailStamp)

    if icsSummary or icsDesc:
        # If ics summary or ics description exist then
        # add them to the message body
        mailStamp.body += buildICSInfo(item, icsSummary, icsDesc)

    #if verbose():
    #    trace("\n\n%s\n\n" % '\n'.join(buf))

    return mailStamp

def buildICSInfo(item, icsSummary, icsDesc):
    buffer = []

    if icsSummary and icsSummary != item.displayName:
        buffer.append(_(u"Title: %(titleText)s") % \
                        {"titleText": icsSummary})

    if icsDesc and icsDesc != item.body:
        buffer.append(_(u"Notes: %(notesText)s") % \
                        {"notesText": icsDesc})

    if not buffer:
        return u""

    if has_stamp(item, EventStamp):
        buffer.insert(0, _(u"\n\nEvent Details\n---"))
    else:
        buffer.insert(0, _(u"\n\nTask Details\n---"))

    return u"\n".join(buffer)


def getChandlerAttachments(messageObject):
    att = {"eimml": [], "ics": []}

    for part in messageObject.walk():
        # multipart/* are just containers
        if part.get_content_maintype() == 'multipart':
            continue

        if part.get_content_type() == "text/calendar":
            att["ics"].append(part.get_payload(decode=True))

        elif part.get_content_type() == "application/eimml":
            att["eimml"].append(part.get_payload(decode=True))

    return att

def _kindToMessageObject(mailStamp):
    """
    This method converts an item stamped as MailStamp to an email message
    string
    a Chandler C{MailMessage} object

    @param mailMessage: A Chandler C{MailMessage}
    @type mailMessage: C{MailMessage}

    @return: C{Message.Message}
    """

    messageObject = Message.Message()

    # Create a messageId if none exists
    mId = getattr(mailStamp, "messageId", None)

    if not mId:
        mId = createMessageID()

    populateHeader(messageObject, 'Message-ID', mId)
    populateEmailAddresses(mailStamp, messageObject)
    populateStaticHeaders(messageObject)

    if hasattr(mailStamp, "dateSentString"):
        date = mailStamp.dateSentString
    else:
        date = dateTimeToRFC2822Date(datetime.now(ICUtzinfo.default))

    messageObject["Date"] = date

    inReplyTo = getattr(mailStamp, "inReplyTo", None)

    subject = mailStamp.subject

    if inReplyTo:
        messageObject["In-Reply-To"] = inReplyTo

    if mailStamp.referencesMID:
        messageObject["References"] = " ".join(mailStamp.referencesMID)

    populateHeader(messageObject, 'Subject', subject, encode=True)

    try:
        payload = getMessageBody(mailStamp)
    except AttributeError:
        payload = u""

    if payload and not payload.endswith(u"\r\n\r\n"):
        # Chandler outgoing messages contain
        # an eimml attachment and an ics attachment
        # if the item is stamped as and Event and
        # or a Task.
        # Many mail readers add attachment icons
        # at the end of the message body.
        # This can be distracting and visually
        # ugly. Appending two line breaks to the
        # payload provides better alignment in
        # mail readers such as Apple Mail and
        # Thunderbird.
        payload += u"\r\n\r\n"

    messageObject.set_type("multipart/mixed")

    # Attach the body text
    mt = MIMEBase64Encode(payload.encode('utf-8'))
    messageObject.attach(mt)

    peers = mailStamp.getRecipients()

    # used for debugging
    #for peer in peers:
    #    print (u"outbound: %s uuid: %s" % (peer.format(),  peer.itsUUID)).encode("utf8")

    # Serialize and attach the eimml can raise ConflictsPending
    eimml = outbound(peers, mailStamp.itsItem, OUTBOUND_FILTERS)

    # EIMML payloads use the 'application' mime main type
    # rather than 'text' to prevent mail viewers from 
    # displaying the EIMML serialized data in-line.
    eimmlPayload = MIMEBase64Encode(eimml, 'application', 'eimml')

    fname = Header.Header(_(u"ChandlerItem.eimml")).encode()
    eimmlPayload.add_header("Content-Disposition", "attachment", filename=fname)
    messageObject.attach(eimmlPayload)

    isEvent = has_stamp(mailStamp, EventStamp)
    isTask  = has_stamp(mailStamp, TaskStamp)

    #XXX There is no attachement support in Preview
    #hasAttachments = mailStamp.getNumberOfAttachments() > 0

    if isEvent or isTask:
        # Format this message as an ICalendar object
        import osaf.sharing.ICalendar as ICalendar
        calendar = ICalendar.itemsToVObject(mailStamp.itsItem.itsView,
                                            [mailStamp.itsItem],
                                            filters=(Remindable.reminders.name,))

        calendar.add('method').value="REQUEST"
        ics = calendar.serialize().encode('utf-8')

        # Attach the ICalendar object
        icsPayload = MIMEBase64Encode(ics, 'text', 'calendar', method='REQUEST')

        fname = Header.Header(_(u"ChandlerItem.ics")).encode()
        icsPayload.add_header("Content-Disposition", "attachment", filename=fname)
        messageObject.attach(icsPayload)

    #XXX: There is no attachement support in Preview via
    # the MailStamp.mimeContent. Commenting out this code
    # for now.
    #
    #if hasAttachments:
    #    attachments = mailStamp.getAttachments()
    #
    #    for attachment in attachments:
    #        if has_stamp(attachment, MailStamp):
    #            # The attachment is another MailMessage
    #            try:
    #                rfc2822 = binaryToData(MailStamp(attachment).rfc2822Message)
    #            except AttributeError:
    #                rfc2822 = kindToMessageText(attachment, False)
    #
    #            message = email.message_from_string(rfc2822)
    #            rfc2822Payload = MIMEMessage(message)
    #            messageObject.attach(rfc2822Payload)
    #
    #        else:
    #            if isinstance(attachment, MIMEText) and \
    #                attachment.mimeType == u"text/calendar":
    #                icsPayload = MIMENonMultipart('text', 'calendar', \
    #                                    method='REQUEST', _charset="utf-8")
    #
    #                fname = Header.Header(attachment.filename).encode()
    #                icsPayload.add_header("Content-Disposition", "attachment", filename=fname)
    #                icsPayload.set_payload(attachment.data.encode('utf-8'))
    #                messageObject.attach(icsPayload)

    return messageObject


def kindToMessageText(mailStamp, saveMessage=False):
    """
    This method converts a email message string to
    a Chandler C{MailMessage} object

    @param mailMessage: A C{email.Message} object representation of a mail message
    @type mailMessage: C{email.Message}
    @param saveMessage: save the message text converted from the C{email.Message}
                        in the mailMessage.rfc2822Message attribute
    @type saveMessage: C{Boolean}
    @return: C{str}
    """

    messageObject = _kindToMessageObject(mailStamp)
    messageText = messageObject.as_string()

    if saveMessage:
        mailStamp.rfc2822Message = dataToBinary(mailStamp, "rfc2822Message",
                                               messageText, 'message/rfc822', 'bz2')

    return messageText

def removeCarriageReturn(text):
    return text.replace("\r", "")

def addCarriageReturn(text):
    # Remove any CRLF that may already be in the text
    text = text.replace("\r\n", "\n")

    # Convert all new lines n the message to CRLF per RFC 822
    return text.replace("\n", "\r\n")


def parseEventInfo(mailStamp):
    assert isinstance(mailStamp, MailStamp)

    if has_stamp(mailStamp.itsItem, EventStamp):
        # The message has been stamped as
        # an event which means its event info has
        # already been populated
        return

    eventStamp = EventStamp(mailStamp.itsItem)
    eventStamp.add()

    # This uses the default Chandler locale determined from
    # the OS or the command line flag --locale (-l)
    startTime, endTime, countFlag, typeFlag = \
                _parseEventInfoForLocale(mailStamp)

    #XXX the parsedatetime API does not always return the
    #    correct parsing results.
    #
    #    Further investigation needs to be done.
    #    What I would like to do is try in the user's current
    #    locale then try in English. But in my testing the
    #    parseText API returns a positive count flag when
    #    if the text contains date time info that does
    #    not match the passed locale. The value of the
    #    startTime and endTime wil be the current users
    #    localtime which is not correct.
    #
    #    I also see incorrect results when text contains
    #    a start and end date. As well as when the
    #    text contains localized times such as 4pm.
    #    In some instances it does correctly parse the time
    #    in others it does not.
    #
    #    The English parsing fallback is commented out till
    #    the above issues are rosolved.
    #
    #if countFlag == 0 and not getLocale().startswith(u"en"):
    #    # Lets try using English language date parsing rules
    #    # as a fallback.
    #    startTime, endTime, countFlag, typeFlag = \
    #               _parseEventInfoForLocale(messageObject, "en")

    if countFlag == 0:
        # No datetime info found in either the mail message subject
        # or the mail message body so do not set any event date time info.
        return

    setEventDateTime(mailStamp.itsItem, startTime,
                     endTime, typeFlag)

def _parseEventInfoForLocale(mailStamp, locale=None):
    try:
        startTime, endTime, countFlag, typeFlag = \
                           parseText(mailStamp.subject, locale)

        if countFlag == 0:
            # No datetime info found im mail message subject
            # so lets try the body
            startTime, endTime, countFlag, typeFlag = \
                              parseText(mailStamp.itsItem.body, locale)
    except Exception, e:
        # The parsedatetime API has some localization bugs that
        # need to be fixed. Capturing Exceptions ensures that
        # the issue does not bubble up to the user as an
        # error message.
        startTime = endTime = countFlag = typeFlag = 0

    return startTime, endTime, countFlag, typeFlag

def parseTaskInfo(mailStamp):
    assert isinstance(mailStamp, MailStamp)

    if has_stamp(mailStamp.itsItem, TaskStamp):
        # The message has already been stamped as
        # a task
        return

    taskStamp = TaskStamp(mailStamp.itsItem)
    taskStamp.add()

def __parseHeaders(view, messageObject, m):
    date = messageObject['Date']

    if date is not None:
        parsed = emailUtils.parsedate_tz(date)

        # It is a non-rfc date string
        if parsed is None:
            if __debug__:
                trace("Message contains a Non-RFC Compliant Date format")

            # Set the sent date to the current Date
            m.dateSent = datetime.now(ICUtzinfo.default)

        else:
            try:
                m.dateSent = datetime.fromtimestamp(emailUtils.mktime_tz(parsed),
                                                    ICUtzinfo.default)
            except:
                m.dateSent = datetime.now(ICUtzinfo.default)

        ##XXX:  Do we need this the tz could be preserved
        m.dateSentString = date

    else:
        m.dateSent = getEmptyDate()
        m.dateSentString = u""

    # reset these values in case they contain info from a previous send
    # or receive
    m.inReplyTo = u""
    m.replyToAddress = None
    m.messageId = u""
    m.fromAddress = None
    m.previousSender = None
    m.headers = {}

    if messageObject['References']:
        refList = messageObject['References'].split()

        for ref in refList:
            ref = ref.strip()
            if ref:
                m.referencesMID.append(ref)

    __assignToKind(view, m, messageObject, 'In-Reply-To', 'String', 'inReplyTo')
    __assignToKind(view, m, messageObject, 'Reply-To', 'EmailAddress', 'replyToAddress')
    __assignToKind(view, m, messageObject, 'Message-ID', 'String', 'messageId', False, False)
    __assignToKind(view, m, messageObject, 'From', 'EmailAddress', 'fromAddress')

    # Capture the previous sender to ensure he or she does not get removed from
    # Edit / Update workflow
    __assignToKind(view, m, messageObject, 'From', 'EmailAddress', 'previousSender')

    for (key, val) in messageObject.items():
        m.headers[getUnicodeValue(key)] = getUnicodeValue(val)

    if not m.fromEIMML:
        # reset these values in case they contain info from a previous send
        # or receive
        m.subject = u""
        m.toAddress = []
        m.ccAddress = []
        m.bccAddress = []

        # These a shared attribute that are managed by the eim layer
        __assignToKind(view, m, messageObject, 'Subject', 'String', 'subject')
        __assignToKind(view, m.toAddress, messageObject, 'To', 'EmailAddressList')
        __assignToKind(view, m.ccAddress, messageObject, 'Cc', 'EmailAddressList')

        # If the message contains no eimml then make the Chandler UI
        # from field match the sender.
        m.originators = hasattr(m, "fromAddress") and [m.fromAddress] or []


def __assignToKind(view, kindVar, messageObject, key,
                   hType, attr=None, decode=True, makeUnicode=True):

    header = messageObject.get(key)

    if header is None:
        return None

    if decode:
        header = decodeHeader(header)
    elif makeUnicode:
        header = getUnicodeValue(header)

    if hType == "String":
        setattr(kindVar, attr, header)

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


def __getEmailAddress(view, name, addr):
    """
    Use any existing EmailAddress, but don't update them
    because that will cause the item to go stale in the UI thread.
    """

    address = EmailAddress.findEmailAddress(view, addr)

    if address is None:
        address = EmailAddress(itsView=view,
                               emailAddress=addr, fullName=name)
    return address


def __parsePart(view, mimePart, parentMIMEContainer, bodyBuffer, counter, buf,
                level=0, compression='bz2'):

    __checkForDefects(mimePart)

    if isinstance(mimePart, str):
        # The mimePart value on bad messages will be
        # individual characters of a message body.
        # This is coming from the Python email package but I believe it is a bug.
        # need to investigate further!
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

    #if verbose():
    #    __trace("message/%s" % subtype, buf, level)

    # If the message is multipart then pass decode=False to
    # get_payload otherwise pass True.
    payload = mimePart.get_payload(decode=not multipart)

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

            bodyBuffer.get('plain').append(u"\n".join(tmp))

        elif __debug__:
            trace("******WARNING****** message/rfc822 part not Multipart investigate")

    elif subtype == "delivery-status":
        # Add the delivery status info to the message body
        bodyBuffer.get('plain').append(getUnicodeValue(mimePart.as_string()))
        return

    elif subtype == "disposition-notification-to":
        # Add the disposition-notification-to info to the message body
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

    #if verbose():
    #    __trace("multipart/%s" % subtype, buf, level)

    # If the message is multipart then pass decode=False to
    # get_poyload otherwise pass True

    payload = mimePart.get_payload(decode=not multipart)
    assert payload is not None, "__handleMultipart payload is None"

    if subtype == "alternative":
        # An alternative container should always have at least one part
        if len(payload) > 0:
            foundText = False
            firstPart = None

            for part in payload:
                if part.get_content_type() == "text/plain":
                    __handleText(view, part, parentMIMEContainer, bodyBuffer,
                                 counter, buf, level+1, compression)
                    foundText = True

                elif firstPart is None and not foundText and not part.is_multipart():
                    # A multipart/alternative container should have
                    # at least one part that is not multipart and
                    # is text based (plain, html, rtf) for display
                    firstPart = part

                elif part.is_multipart():
                    # If we find a multipart sub-part with in the alternative
                    # part handle it
                    __handleMultipart(view, part, parentMIMEContainer, bodyBuffer, \
                                      counter, buf, level+1, compression)

            if not foundText and firstPart is not None:
                if firstPart.get_content_maintype() == "text":
                    __handleText(view, firstPart, parentMIMEContainer,
                                 bodyBuffer, counter, buf, level+1, compression)
                else:
                    __handleBinary(view, firstPart, parentMIMEContainer, counter, 
                                   buf, level+1, compression)
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

    #if verbose():
    #    __trace(contype, buf, level)

    # skip AppleDouble resource files per RFC1740
    if contype == "application/applefile":
        return

    mimeBinary = MIMEBinary(itsView=view)

    # Get the attachments data
    data = mimePart.get_payload(decode=1)
    assert data is not None, "__handleBinary data is None"

    mimeBinary.filesize = len(data)
    mimeBinary.filename = __getFileName(mimePart, counter)
    mimeBinary.mimeType = contype

    # Try to figure out what the real mimetype is
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

    #if verbose():
    #    __trace("text/%s" % subtype, buf, level)

    # Get the attachment data
    body = mimePart.get_payload(decode=1)

    size = len(body)

    charset = mimePart.get_content_charset("utf-8")

    if size and (subtype == "plain" or subtype == "rfc822-headers"):
        bodyBuffer.get('plain').append(getUnicodeValue(body, charset,ignore=True))

    else:
        if size and subtype == "html" and len(bodyBuffer.get('plain')) == 0:
            bodyBuffer.get('html').append(getUnicodeValue(body, charset, ignore=True))

        if IGNORE_ATTACHMENTS:
            return

        mimeText = MIMEText(itsView=view)
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

    # No Filename need to create an arbitrary name
    ext = mimetypes.guess_extension(mimePart.get_content_type())

    if not ext:
        ext = '.bin'

    return u'Attachment-%s%s' % (counter.nextValue(), ext)

def __checkForDefects(mimePart):
    if __debug__ and len(mimePart.defects) > 0:
        strBuffer = [mimePart.get("Message-ID", "Unknown Message ID")]
        handled = False

        for defect in mimePart.defects:
            # Just get the class name strip the package path
            defectName = str(defect.__class__).split(".").pop()

            if not handled and \
              (defectName == "MultipartInvariantViolationDefect" or \
               defectName == "NoBoundaryInMultipartDefect" or \
               defectName == "StartBoundaryNotFoundDefect"):

                # The Multipart Body of the message is corrupted or
                # inaccurate(Spam?) convert the payload to a text part.
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
