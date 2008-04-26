#   Copyright (c) 2005-2007 Open Source Applications Foundation
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
from email.MIMEMultipart import MIMEMultipart
from email.MIMENonMultipart import MIMENonMultipart
import logging
import mimetypes
from datetime import datetime


#Chandler imports
from osaf.pim.mail import EmailAddress, MailMessage, MIMEText, MIMEBinary, \
                          getMessageBody, getCurrentMeEmailAddresses, \
                          getRecurrenceMailStamps, addressMatchGenerator, \
                          isMeAddress

from osaf.pim.calendar.Calendar import parseText, setEventDateTime
from osaf.pim import has_stamp, TaskStamp, EventStamp, MailStamp, Remindable
from i18n import ChandlerMessageFactory as _
from osaf.sharing import (getFilter, errors as sharingErrors, inbound, outbound,
                          checkTriageOnly, SharedItem)

#Chandler Mail Service imports
import constants
from constants import IGNORE_ATTACHMENTS
from utils import *
from utils import Counter

__all__ = ['messageTextToKind', 'kindToMessageText']


OUTBOUND_FILTERS = getFilter(['cid:triage-filter@osaf.us', 'cid:event-status-filter@osaf.us',
                              'cid:reminders-filter@osaf.us', 'cid:bcc-filter@osaf.us',
                              'cid:dateSent-filter@osaf.us', 'cid:headers-filter@osaf.us',
                              'cid:inReplyTo-filter@osaf.us', 'cid:references-filter@osaf.us',
                              'cid:messageId-filter@osaf.us', 'cid:mimeContent-filter@osaf.us',
                              'cid:rfc2822Message-filter@osaf.us', 'cid:previousSender-filter@osaf.us',
                              'cid:messageState-filter@osaf.us', 'cid:replyToAddress-filter@osaf.us',])

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

    except(UnicodeError, UnicodeDecodeError, LookupError, \
           email.errors.HeaderParseError):
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


def messageTextToKind(view, messageText):
    """
    This method converts a email message string to
    a Chandler C{MailMessage} object

    @param messageText: A string representation of a mail message
    @type messageText: string
    @return: C{MailMessage}
    """

    assert isinstance(messageText, str), "messageText must be a String"

    return messageObjectToKind(view, email.message_from_string(messageText),
                               messageText)

def getPeer(view, messageObject):
    # Get the from address ie. Sender.
    emailAddr = messageObject.get("From")

    if not emailAddr:
        return None

    name, addr = emailUtils.parseaddr(emailAddr)

    return EmailAddress.getEmailAddress(view, getUnicodeValue(addr), decodeHeader(name))


def messageObjectToKind(view, messageObject, messageText=None):
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

    chandlerAttachments = getChandlerAttachments(messageObject)

    if chandlerAttachments["eimml"]:
        eimml = chandlerAttachments["eimml"][0]
        peer = getPeer(view, messageObject)

        if peer is None:
            # A peer address is required for eimml
            # deserialization. If there is no peer
            # then ignore the eimml data and return
            # an error flag.
            return (-1, None)

        matchingAddresses = []

        for address in addressMatchGenerator(peer):
            matchingAddresses.append(address)

        # the matchingAddresses list will at least contain the
        # peer address since it is an EmailAddress Item and
        # there for will be in the EmailAddressCollection index.
        statusCode, mailStamp = parseEIMML(view, peer, matchingAddresses, eimml)

        if statusCode != 1:
            # There was either an error during
            # processing of the eimml or the
            # eimml was older than the current
            # Item's state so it was ignored.
            return (statusCode, None)

    elif chandlerAttachments["ics"]:
        ics = chandlerAttachments["ics"][0]

        result = parseICS(view, ics, messageObject)

        if result is not None:
            # If the result is None then there
            # was an error that prevented converting
            # the ics text to a Chandler Item
            # in which case the ics is ignored and
            # the rest of the message parsed.
            mailStamp, icsDesc, icsSummary = result

    if not mailStamp:
        mailStamp = MailMessage(itsView=view)
        mailStamp.fromEIMML = False

    if not IGNORE_ATTACHMENTS:
        # Save the original message text in a text blob
        if messageText is None:
            messageText = messageObject.as_string()

        mailStamp.rfc2822Message = dataToBinary(mailStamp, "rfc2822Message", messageText,
                                               'message/rfc822', 'bz2', False)

    if getattr(mailStamp, "messageId", None):
        # The presence a messageId indicated that
        # this message has already been sent or
        # received and thus has been updated.
        mailStamp.isUpdated = True

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

        if IGNORE_ATTACHMENTS:
            counter = None
        else:
            counter = Counter()

        bodyBuffer = {'plain': [], 'html': []}
        buf = None

        # The body of the message will be contained in the eimml so
        # do not try and parse the mail message body.
        __parsePart(view, messageObject, mailStamp, bodyBuffer, counter, buf)

        mailStamp.body = buildBody(bodyBuffer)

    __parseHeaders(view, messageObject, mailStamp, True, True)

    if icsSummary or icsDesc:
        # If ics summary or ics description exist then
        # add them to the message body
        mailStamp.body += buildICSInfo(mailStamp, icsSummary, icsDesc)

    #if verbose():
    #    trace("\n\n%s\n\n" % '\n'.join(buf))

    return (1, mailStamp)

def parseEIMML(view, peer, matchingAddresses, eimml):
    if isMeAddress(peer):
        # If the Chandler EIMML message is from me then
        # ignore it.
        return (0, None)

    try:
        item = inbound(matchingAddresses, eimml)

        mailStamp = MailStamp(item)
        mailStamp.fromEIMML = True

        return (1, mailStamp)

    except sharingErrors.MalformedData, e:
        # The eimml records contained bogus
        # syntax and will not be processed
        # Raising an error here would result
        # in the entire mail download being
        # terminated so we log the error
        # instead
        logging.exception(e)
        return (-1, None)

    except sharingErrors.OutOfSequence, e1:
        # The eimml records are older then
        # the current state and are not going
        # to be applied so return None
        return (0, None)

    except Exception, e2:
        # There was an error at the XML parsing layer.
        # Log the error and continue to download.
        logging.exception(e2)
        return (-1, None)

def parseICS(view, ics, messageObject=None):

    from osaf.sharing import (deserialize, SharingTranslator, ICSSerializer,
                              remindersFilter)


    icsDesc = icsSummary = None

    peer = None
    if messageObject is not None:
        peer = getPeer(view, messageObject)
    if peer is None:
        # we don't really need a valid peer to import icalendar, make one up
        peer = EmailAddress.getEmailAddress(view, "empty@example.com")

    try:
        items = deserialize(view, peer, ics, SharingTranslator,
                            ICSSerializer, filter=remindersFilter)
    except Exception, e:
        logging.exception(e)
        return None

    if len(items) > 0:
        # We got something - stamp the first thing as a MailMessage
        # and use it. (If it was an existing event, we'll reuse it.)
        item = items[0]
        # use the master, if a modification happens to be the first item
        item = getattr(item, 'inheritFrom', item)

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
                ms = MailStamp(item)
                ms.add()

        mailStamp = MailStamp(item)
        mailStamp.fromEIMML = False

        return (mailStamp, icsDesc, icsSummary)

    return None

def buildBody(bodyBuffer):
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

    return body


def buildICSInfo(mailStamp, icsSummary, icsDesc):
    buffer = []

    item = mailStamp.itsItem

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

def previewQuickConvert(view, headers, body, eimml, ics):
        # 1.0 Case
        #  1. Standard mail message
        #      a. headers (build a decoded headers dict using m.keys())
        #      b. body
        #  2. ICS
        #      a. headers (build a decoded headers dict using m.keys())
        #      b. body
        #      c. decoded ics attachment
        #  3. EIM
        #      a. headers (build a decoded headers dict using m.keys())
        #      b. decoded eim attachment

    mailStamp = icsDesc = icsSummary = None

    if eimml:
        # Get the from address ie. Sender.
        emailAddr = headers.get("From")

        if not emailAddr:
            # A peer address is required for eimml
            # deserialization. If there is no peer
            # then ignore the eimml data.
            return (-1, None)

        name, addr = emailUtils.parseaddr(emailAddr)
        peer = EmailAddress.getEmailAddress(view, addr, name)

        matchingAddresses = []

        for address in addressMatchGenerator(peer):
            matchingAddresses.append(address)

        # the matchingAddresses list will at least contain the
        # peer address since it is an EmailAddress Item and
        # there for will be in the EmailAddressCollection index.
        statusCode, mailStamp = parseEIMML(view, peer, matchingAddresses, eimml)

        if statusCode != 1:
            # There was either an error during
            # processing of the eimml or the
            # eimml was older than the current
            # Item's state so it was ignored.
            return (statusCode, None)

    elif ics:
        result = parseICS(view, ics)

        if result is not None:
            # If the result is None then there
            # was an error that prevented converting
            # the ics text to a Chandler Item
            # in which case the ics is ignored and
            # the rest of the message parsed.
            mailStamp, icsDesc, icsSummary = result

    if not mailStamp:
        mailStamp = MailMessage(itsView=view)
        mailStamp.fromEIMML = False

    if getattr(mailStamp, "messageId", None):
        # The presence a messageId indicated that
        # this message has already been sent or
        # received and thus is an update.
        mailStamp.isUpdated = True

    # Setting these values here reduces Observer
    # processing time when calculating if the
    # message should appear in the In Collection
    mailStamp.viaMailService = True
    # Look at the from address if it matches a me address
    # and the ignore me attribute enabled then set toMe to
    # false otherwise set to True

    mailStamp.toMe = True

    if not mailStamp.fromEIMML:
        mailStamp.body = body

    if icsSummary or icsDesc:
        # If ics summary or ics description exist then
        # add them to the message body
        mailStamp.body += buildICSInfo(mailStamp, icsSummary, icsDesc)

    __parseHeaders(view, headers, mailStamp, False, False)

    return (1, mailStamp)

def previewQuickParse(msg, isObject=False):
    # Returns a tuple:
    #    0: headers dict decoded and converted to unicode
    #    1: body of the message ready for assigning to the
    #       ContentItem.body attribute or None
    #    2: eim attachment decode and strip of carriage returns
    #       or None
    #    3: ics attachment decode and strip of carriage returns
    #       or None

    headers = body = eimml = ics = None

    if not isObject:
        msgObj = email.message_from_string(msg)
    else:
        msgObj = msg

    headers = Message.Message()

    for key, val in msgObj.items():
        headers[getUnicodeValue(key)] = decodeHeader(val)

    att = getChandlerAttachments(msgObj)

    if att["eimml"]:
        eimml = att['eimml'][0]
    else:
        bodyBuffer = {'plain': [], 'html': []}
        __parsePart(None, msgObj, None, bodyBuffer, None, None)

        body = buildBody(bodyBuffer)

        if att['ics']:
            ics = att['ics'][0]

    return (headers, body, eimml, ics)

def getChandlerAttachments(messageObject):
    att = {"eimml": [], "ics": []}

    for part in messageObject.walk():
        # multipart/* are just containers
        if part.get_content_maintype() == 'multipart':
            continue

        if part.get_content_type() == "text/calendar":
            att["ics"].append(removeCarriageReturn(part.get_payload(decode=True)))

        elif part.get_content_type() == "text/eimml":
            att["eimml"].append(removeCarriageReturn(part.get_payload(decode=True)))

    return att

def kindToMessageObject(mailStamp):
    """
    This method converts an item stamped as MailStamp to an email message
    string
    a Chandler C{MailMessage} object

    @param mailMessage: A Chandler C{MailMessage}
    @type mailMessage: C{MailMessage}

    @return: C{Message.Message}
    """

    view = mailStamp.itsItem.itsView

    mailStampOccurrence, mailStampMaster = getRecurrenceMailStamps(mailStamp)

    isEvent = has_stamp(mailStampOccurrence, EventStamp)
    isTask  = has_stamp(mailStampOccurrence, TaskStamp)

    messageObject = Message.Message()

    # Create a messageId if none exists
    mId = getattr(mailStampMaster, "messageId", None)

    if not mId:
        mId = createMessageID()

    populateHeader(messageObject, 'Message-ID', mId)
    populateEmailAddresses(mailStampMaster, messageObject)
    populateStaticHeaders(messageObject)

    if hasattr(mailStampMaster, "dateSentString"):
        date = mailStampMaster.dateSentString
    else:
        date = dateTimeToRFC2822Date(datetime.now(view.tzinfo.default))

    messageObject["Date"] = date

    inReplyTo = getattr(mailStampMaster, "inReplyTo", None)

    subject = mailStampOccurrence.subject

    if subject is not None:
        # Fixes bug 10254 where the title of a Item 
        # that contained a new line was breaking the 
        # the rfc2822 formatting of the outgoing message.
        subject = subject.replace("\n", "")

    if inReplyTo:
        messageObject["In-Reply-To"] = inReplyTo

    if mailStampMaster.referencesMID:
        messageObject["References"] = " ".join(mailStampMaster.referencesMID)

    populateHeader(messageObject, 'Subject', subject, encode=True)

    try:
        payload = getMessageBody(mailStampOccurrence)
    except AttributeError:
        payload = u""

    if isTask or isEvent and payload and \
        not payload.endswith(u"\r\n\r\n"):
        # Chandler outgoing Tasks and Events contain
        # an ics attachment.
        # Many mail readers add attachment icons
        # at the end of the message body.
        # This can be distracting and visually
        # ugly. Appending two line breaks to the
        # payload provides better alignment in
        # mail readers such as Apple Mail and
        # Thunderbird.
        payload += u"\r\n\r\n"

    messageObject.set_type("multipart/mixed")

    # Create a multipart/alernative MIME Part
    # that will contain the Chandler eimml and
    # the body of the message as alternative
    # parts. Doing this prevents users from seeing
    # the Chandler eimml which is machine readable
    # xml code and is not displayable to the user.
    alternative = MIMEMultipart("alternative")

    # Serialize and attach the eimml can raise ConflictsPending
    eimml = outbound(getPeers(mailStampMaster), mailStampMaster.itsItem,
                     OUTBOUND_FILTERS)

    eimmlPayload = MIMEBase64Encode(eimml, 'text', 'eimml')

    # Since alternative parts are in order from least
    # renderable to most renderable add the eimml payload
    # first.
    alternative.attach(eimmlPayload)

    # Attach the body text
    mt = MIMEBase64Encode(payload.encode('utf-8'))

    # Add the email body text to the alternative part
    alternative.attach(mt)

    # Add the alternative part to the mail multipart/mixed
    # main content type.
    messageObject.attach(alternative)


    #XXX There is no attachement support in 1.0
    #hasAttachments = mailStamp.getNumberOfAttachments() > 0

    if isEvent or isTask:
        # Format this message as an ICalendar object
        from osaf.sharing import (serialize, VObjectSerializer,
                                  SharingTranslator, remindersFilter)
        items = [mailStampMaster.itsItem]
        for mod in EventStamp(mailStampMaster).modifications or []:
            if not checkTriageOnly(mod):
                items.append(mod)

        calendar = serialize(mailStamp.itsItem.itsView,
                             items,
                             SharingTranslator,
                             VObjectSerializer,
                             filter=remindersFilter)

        # don't use method REQUEST because it will cause Apple iCal to treat
        # the ics attachment as iMIP
        calendar.add('method').value="PUBLISH"
        ics = calendar.serialize().encode('utf-8')

        # Attach the ICalendar object
        icsPayload = MIMEBase64Encode(ics, 'text', 'calendar', method='PUBLISH')

        # L10N: The filename of Events and Tasks emailed from Chandler
        fname = Header.Header(_(u"ChandlerItem.ics")).encode()
        icsPayload.add_header("Content-Disposition", "attachment", filename=fname)
        messageObject.attach(icsPayload)

    #XXX: There is no attachment support in 1.0 via
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

    messageObject = kindToMessageObject(mailStamp)
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


def getPeers(mailStamp):
    peers = mailStamp.getRecipients()

    # First, make sure we don't have peers with duplicate email addresses
    peerAddresses = set()
    filteredPeers = list()

    for peer in peers:
        address = getattr(peer, 'emailAddress', '')

        if address and address not in peerAddresses:
            # Note: shouldn't we also filter out "me" addresses?  I guess it's
            # harmless not to since we ignore incoming EIMML messages that are
            # "from me".
            peerAddresses.add(address)
            filteredPeers.append(peer)

    peers = filteredPeers

    # Next, for each peer already associated with the item, if any of them have
    # email addresses which match the 'peers' list, there is a chance that the
    # new peer is actually an EmailAddress item with same address but different
    # name.  We want to swap that peer out for the one already associated with
    # the item.
    item = mailStamp.itsItem
    view = item.itsView

    if has_stamp(item, SharedItem):
        shared = SharedItem(item)
        updatedPeers = list()

        # Build a set of email addresses already associated with this item
        associatedAddresses = set()
        addressMapping = {}

        for state in getattr(shared, "peerStates", []):
            peerUUID = shared.peerStates.getAlias(state)
            peer = view.findUUID(peerUUID)

            if peer is not None and getattr(peer, 'emailAddress', ''):
                associatedAddresses.add(peer.emailAddress)
                addressMapping[peer.emailAddress] = peer

        # Look for matches between already associated and new:
        for peer in peers:
            if peer.emailAddress in associatedAddresses:
                if shared.getPeerState(peer, create=False) is not None:
                    # We have a perfect match
                    updatedPeers.append(peer)
                else:
                    # address matches, but wrong email address item; switch
                    # to the already associated one
                    updatedPeers.append(addressMapping[peer.emailAddress])
            else:
                # No matching address; it's a new peer
                updatedPeers.append(peer)

        peers = updatedPeers

    return peers


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
        view = mailStamp.itsItem.itsView
        startTime, endTime, countFlag, typeFlag = \
                           parseText(view, mailStamp.subject, locale)

        if countFlag == 0:
            # No datetime info found im mail message subject
            # so lets try the body
            startTime, endTime, countFlag, typeFlag = \
                              parseText(view, mailStamp.itsItem.body, locale)
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

def __parseHeaders(view, messageObject, m, decode, makeUnicode):
    date = messageObject['Date']

    if date is not None:
        parsed = emailUtils.parsedate_tz(date)

        # It is a non-rfc date string
        if parsed is None:
            # Set the sent date to the current Date
            m.dateSent = datetime.now(view.tzinfo.default)

        else:
            try:
                m.dateSent = datetime.fromtimestamp(emailUtils.mktime_tz(parsed),
                                                    view.tzinfo.default)
            except:
                m.dateSent = datetime.now(view.tzinfo.default)

        m.dateSentString = date

    else:
        m.dateSent = getEmptyDate(view)
        m.dateSentString = u""

    # reset these values in case they contain info from a previous send
    # or receive
    m.inReplyTo = u""
    m.replyToAddress = None
    m.messageId = u""
    m.fromAddress = None
    m.previousSender = None
    m.headers = {}
    m.referencesMID = []

    if messageObject['References']:
        refList = messageObject['References'].split()

        for ref in refList:
            ref = ref.strip()
            if ref:
                m.referencesMID.append(ref)

    __assignToKind(view, m, messageObject, 'In-Reply-To', 'String', 'inReplyTo', decode, makeUnicode)
    __assignToKind(view, m, messageObject, 'Reply-To', 'EmailAddress', 'replyToAddress', decode, makeUnicode)
    __assignToKind(view, m, messageObject, 'Message-ID', 'String', 'messageId', False, False)
    __assignToKind(view, m, messageObject, 'From', 'EmailAddress', 'fromAddress', decode, makeUnicode)

    # Capture the previous sender to ensure he or she does not get removed from
    # Edit / Update workflow
    __assignToKind(view, m, messageObject, 'From', 'EmailAddress', 'previousSender', decode, makeUnicode)

    for (key, val) in messageObject.items():
        if makeUnicode:
            key = getUnicodeValue(key)
            val = getUnicodeValue(val)

        m.headers[key] = val

    if not m.fromEIMML:
        # reset these values in case they contain info from a previous send
        # or receive
        m.subject = u""
        m.toAddress = []
        m.ccAddress = []
        m.bccAddress = []

        # These a shared attribute that are managed by the eim layer
        __assignToKind(view, m, messageObject, 'Subject', 'String', 'subject', decode, makeUnicode)
        __assignToKind(view, m.toAddress, messageObject, 'To', 'EmailAddressList', None, decode, makeUnicode)
        __assignToKind(view, m.ccAddress, messageObject, 'Cc', 'EmailAddressList', None, decode, makeUnicode)

        # If the message contains no eimml then make the Chandler UI
        # from field match the sender.
        m.originators = hasattr(m, "fromAddress") and [m.fromAddress] or []


def __assignToKind(view, kindVar, messageObject, key, hType, attr, decode, makeUnicode):
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

        if decode:
            name = decodeHeader(name)

        if makeUnicode:
            addr = getUnicodeValue(addr)

        ea = EmailAddress.getEmailAddress(view, addr, name)

        if ea is not None:
            setattr(kindVar, attr, ea)

    elif hType == "EmailAddressList":
        for name, addr in emailUtils.getaddresses(messageObject.get_all(key, [])):
            if decode:
                name = decodeHeader(name)

            if makeUnicode:
                addr = getUnicodeValue(addr)

            ea = EmailAddress.getEmailAddress(view, addr, name)

            if ea is not None:
                kindVar.append(ea)

def __parsePart(view, mimePart, parentMIMEContainer, bodyBuffer, counter, buf,
                level=0):

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
                        counter, buf, level)

    elif maintype == "multipart":
        __handleMultipart(view, mimePart, parentMIMEContainer, bodyBuffer,
                          counter, buf, level)

    elif maintype == "text":
        __handleText(view, mimePart, parentMIMEContainer, bodyBuffer,
                     counter, buf, level)

    else:
        __handleBinary(view, mimePart, parentMIMEContainer,
                       counter, buf, level)


def __handleMessage(view, mimePart, parentMIMEContainer, bodyBuffer,
                    counter, buf, level):
    subtype = mimePart.get_content_subtype()
    multipart = mimePart.is_multipart()

    #if verbose():
    #    __trace("message/%s" % subtype, buf, level)


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
        # Since the mime part is multipart pass decode=False
        payload = mimePart.get_payload(decode=False)

        for part in payload:
            __parsePart(view, part, parentMIMEContainer, bodyBuffer,
                        counter, buf, level+1)

    elif __debug__:
        trace("******WARNING****** message/%s payload not multipart" % subtype)


def __handleMultipart(view, mimePart, parentMIMEContainer, bodyBuffer,
                      counter, buf, level):
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
                                 counter, buf, level+1)
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
                                      counter, buf, level+1)

            if not foundText and firstPart is not None:
                if firstPart.get_content_maintype() == "text":
                    __handleText(view, firstPart, parentMIMEContainer,
                                 bodyBuffer, counter, buf, level+1)
                else:
                    __handleBinary(view, firstPart, parentMIMEContainer, counter,
                                   buf, level+1)
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
                        counter, buf, level+1)


def __handleBinary(view, mimePart, parentMIMEContainer,
                   counter, buf, level):

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
    data = mimePart.get_payload(decode=True)
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
                                   mimeBinary.mimeType)

    parentMIMEContainer.mimeParts.append(mimeBinary.itsItem)

def __handleText(view, mimePart, parentMIMEContainer, bodyBuffer,
                 counter, buf, level):
    subtype = mimePart.get_content_subtype()

    #if verbose():
    #    __trace("text/%s" % subtype, buf, level)

    # Get the attachment data
    body = mimePart.get_payload(decode=True)

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
