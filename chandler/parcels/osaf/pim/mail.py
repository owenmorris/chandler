#   Copyright (c) 2003-2006 Open Source Applications Foundation
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


"""
Classes used for Mail parcel kinds.
"""

__all__ = (
    'AccountBase', 'CommunicationStatus', 'DownloadAccountBase', 'EmailAddress',
    'IMAPAccount', 'IMAPDelivery', 'MIMEBase', 'MIMEBinary', 'MIMEContainer',
    'MIMENote', 'MIMESecurity', 'MIMEText', 'MailDeliveryBase',
    'MailDeliveryError', 'MailMessage', 'MailStamp', 'POPAccount',
    'POPDelivery', 'SMTPAccount', 'SMTPDelivery', 'replyToMessage',
    'replyAllToMessage', 'forwardMessage', 'getCurrentSMTPAccount',
    'getCurrentMailAccount', 'ACCOUNT_TYPES'
)


import application
from application import schema
import repository.item.Item as Item
import items, notes, stamping, collections
import email.Utils as Utils
import re as re
import chandlerdb.item.ItemError as ItemError
from chandlerdb.util.c import UUID
import PyICU


from repository.util.Path import Path
from i18n import ChandlerMessageFactory as _
from osaf import messages
from repository.persistence.RepositoryError import RepositoryError, VersionConflictError
from osaf.pim.calendar import EventStamp
from osaf.pim import Remindable

"""

ISSUES:
===========
1. Why is from check getting called with invalid address and then called again. The first call
   is always the current me address wierd.

TO DO:
=========
1. Rethink MailDeliveryError logic
2. Reread POP spec for UID logic
3. Rename messageDownloadSequence

Design Issues:
      1. Is tries really needed
      2. Date sent string could probally be gotten rid of
"""

def __populateBody(mailStamp, bodyHeader=u"", includeMailHeaders=False, includeEventInfo=False):

    buffer = [bodyHeader]

    addr = mailStamp.fromAddress

    if includeMailHeaders:
        buffer.append(u"> From: %s" % EmailAddress.format(mailStamp.fromAddress))

        if mailStamp.replyToAddress:
            buffer.append(u"> Reply-To: %s" % EmailAddress.format(mailStamp.replyToAddress))

        to = []

        for addr in mailStamp.toAddress:
            to.append(EmailAddress.format(addr))

        buffer.append(u"> To: %s" % ", ".join(to))

        if len(mailStamp.ccAddress):
            cc = []
            for addr in mailStamp.ccAddress:
                cc.append(EmailAddress.format(addr))

            buffer.append(u"> Cc: %s" % ", ".join(cc))

        m = PyICU.DateFormat.createDateTimeInstance(PyICU.DateFormat.kMedium)

        dateSent = _(u"Sent: %(dateSent)s") % {'dateSent': m.format(mailStamp.dateSent)}
        buffer.append(u"> %s" % dateSent)

        # add an additional new line
        buffer.append(u"> ")

    if includeEventInfo:
        event = EventStamp(mailStamp.itsItem)

        tmpBuffer = []
        tmpBuffer.append(_(u"Title: %(eventTitle)s") % {'eventTitle': mailStamp.itsItem.displayName})

        try:
            location = unicode(getattr(event, 'location', u''))

            if len(location.strip()) > 0:
                tmpBuffer.append(_(u"Location: %(eventLocation)s") % {'eventLocation': location})
        except AttributeError:
            pass

        try:
            date = event.getTimeDescription()
            tmpBuffer.append(_(u"Date: %(eventDate)s") % {'eventDate': date})
        except AttributeError:
            pass

        try:
            choices = {
                     u'confirmed': _(u'Confirmed'),
                     u'tentative': _(u'Tentative'),
                     u'fyi': _(u'FYI'),
                      }

            status = choices[event.transparency]


            tmpBuffer.append(_(u"Status: %(eventStatus)s") % {'eventStatus': status})
        except AttributeError:
            pass

        try:
            r = Remindable(mailStamp.itsItem)
            alarm = r.getNextReminderTime()

            if alarm and len(r.reminders):
                m = PyICU.DateFormat.createDateTimeInstance(PyICU.DateFormat.kMedium)
                tmpBuffer.append(_(u"Alarm: %(eventAlarm)s") % {'eventAlarm': m.format(alarm)})
        except AttributeError:
            pass

        for line in tmpBuffer:
            # Add the '> ' reply to mail token
            buffer.append(u"> %s" % line)

        buffer.append(u"")

    origBody = mailStamp.body.split(u"\n")

    for line in origBody:
        if line.startswith(u">"):
            buffer.append(u">%s" % line)
        else:
            buffer.append(u"> %s" % line)

    return u"\n".join(buffer)


def __actionOnMessage(view, mailStamp, action="REPLY"):
    assert(isinstance(mailStamp, MailStamp))
    assert(action == "REPLY" or action == "REPLYALL" or action == "FORWARD")

    newMailStamp = MailMessage(itsView=view)
    newMailStamp.InitOutgoingAttributes()

    hasEvent = stamping.has_stamp(mailStamp.itsItem, EventStamp)

    #This could be None
    newMailStamp.fromAddress = EmailAddress.getCurrentMeEmailAddress(view)

    if action == "REPLY" or action == "REPLYALL":
        if mailStamp.subject:
            if mailStamp.subject.lower().startswith(u"re: "):
                newMailStamp.subject = mailStamp.subject
            else:
                newMailStamp.subject = u"Re: %s" % mailStamp.subject

        newMailStamp.inReplyTo = mailStamp.messageId
        newMailStamp.referencesMID.extend(mailStamp.referencesMID)
        newMailStamp.referencesMID.append(mailStamp.messageId)

        m = PyICU.DateFormat.createDateInstance(PyICU.DateFormat.kMedium)

        bodyHeader = u"\n\n"

        addr = mailStamp.fromAddress
        txt = addr.fullName and addr.fullName or addr.emailAddress

        bodyHeader += _(u"On %(date)s, %(emailAddress)s said:\n") % \
                       {'date': m.format(mailStamp.dateSent),
                        'emailAddress': txt}

        newMailStamp.body = __populateBody(mailStamp, bodyHeader, includeEventInfo=hasEvent)

        to = mailStamp.replyToAddress and mailStamp.replyToAddress or \
             mailStamp.fromAddress

        newMailStamp.toAddress.append(to)

        if action == "REPLYALL":
            addresses = {}

            #The from address can be empty if no account info has been
            #configured
            if newMailStamp.fromAddress:
                addresses[newMailStamp.fromAddress.emailAddress] = True

            for addr in newMailStamp.toAddress:
                addresses[addr.emailAddress] = True

            for addr in mailStamp.toAddress:
                if not addresses.has_key(addr.emailAddress):
                    newMailStamp.ccAddress.append(addr)
                    addresses[addr.emailAddress] = True

            for addr in mailStamp.ccAddress:
                if not addresses.has_key(addr.emailAddress):
                    newMailStamp.ccAddress.append(addr)
                    addresses[addr.emailAddress] = True
    else:
        #FORWARD CASE
        if mailStamp.subject:
            if mailStamp.subject.lower().startswith(u"fwd: ") or \
               mailStamp.subject.lower().startswith(u"[fwd: "):
                newMailStamp.subject = mailStamp.subject
            else:
                newMailStamp.subject = u"Fwd: %s" % mailStamp.subject

        if hasEvent:
            import osaf.sharing.ICalendar as ICalendar
            event = EventStamp(mailStamp.itsItem)
            calendar = ICalendar.itemsToVObject(view, [event],
                           filters=(Remindable.reminders.name,))
            
            # it's possibly more accurate to use a REQUEST method instead of
            # PUBLISH, but as long as we don't include ATTENDEES, this causes
            # problems for iCal, so setting the method to PUBLISH for now (bug 7478)
            calendar.add('method').value="PUBLISH"
            ics = calendar.serialize()
            icsName = u"%s.ics" % mailStamp.itsItem.displayName

            attachment = MIMEText(itsView=view)
            attachment.filename = icsName
            attachment.filesize = long(len(ics))
            attachment.mimeType = "text/calendar"
            attachment.data = ics

            newMailStamp.mimeContent.mimeParts.append(attachment)

            bodyHeader = _(u"1 attachment: %(attachmentName)s\nType your forward message here:\n\n\nBegin forwarded message:") % {'attachmentName': icsName}
        else:
            bodyHeader = _(u"Type your forward message here:\n\nBegin forwarded message:")

        newMailStamp.body = __populateBody(mailStamp, bodyHeader, True, hasEvent)

    #add to dashboard by making mine
    schema.ns('osaf.pim', view).allCollection.add(newMailStamp.itsItem)
    newMailStamp.itsItem.mine = True

    try:
        view.commit()
    except RepositoryError, e:
        raise
    except VersionConflictError, e:
        raise

    return newMailStamp.itsItem

def replyToMessage(view, mailStamp):
    """
        @return: a C{Note} item which has been stamped as a c{MailStamp}
    """
    return __actionOnMessage(view, mailStamp, "REPLY")

def replyAllToMessage(view, mailStamp):
    """
        @return: a C{Note} item which has been stamped as a c{MailStamp}
    """
    return __actionOnMessage(view, mailStamp, "REPLYALL")

def forwardMessage(view, mailStamp):
    """
        @return: a C{Note} item which has been stamped as a c{MailStamp}
    """
    return __actionOnMessage(view, mailStamp, "FORWARD")


def checkIfToMe(mailStamp, type):
    assert(isinstance(mailStamp, MailStamp))

    view = mailStamp.itsItem.itsView

    meAddressCollection = schema.ns("osaf.pim", view).meAddressCollection

    found = False

    if type == 0:
        for addr in mailStamp.toAddress:
            if EmailAddress.findEmailAddress(view, addr.emailAddress, meAddressCollection):
                found = True
                break

    elif type == 1:
        if mailStamp.ccAddress:
            for addr in mailStamp.ccAddress:
                if EmailAddress.findEmailAddress(view, addr.emailAddress, meAddressCollection):
                    found = True
                    break
    else:
        #invalid type passed
        return

    if found != mailStamp.toMe:
        mailStamp.toMe = found

def checkIfFromMe(mailStamp, type):
    assert(isinstance(mailStamp, MailStamp))

    view = mailStamp.itsItem.itsView

    meAddressCollection = schema.ns("osaf.pim", view).meAddressCollection

    found = False

    if type == 0:
        if mailStamp.fromAddress is not None and \
           EmailAddress.findEmailAddress(view, mailStamp.fromAddress.emailAddress, \
                                         meAddressCollection):
            found = True

    elif type == 1:
        if mailStamp.replyToAddress != None and \
           EmailAddress.findEmailAddress(view, mailStamp.replyToAddress.emailAddress, \
                                         meAddressCollection):
            found = True
    else:
        #invalid type passed
        return

    if found != mailStamp.fromMe:
        mailStamp.fromMe = found

def getCurrentSMTPAccount(view, uuid=None, includeInactives=False):
    """
    This function returns a tuple containing:
     1. The an C{SMTPAccount} account
     2. The ReplyTo C{EmailAddress} associated with the C{SMTPAccounts}
        parent which will either be a POP or IMAP Acccount.

    @param uuid: The C{uuid} of the C{SMTPAccount}. If no C{uuid} passed will return
                 the current  C{SMTPAccount}
    @type uuid: C{uuid}
    @return C{tuple} in the form (C{SMTPAccount}, C{EmailAddress})
    """

    smtpAccount = None
    replyToAddress = None

    if uuid is not None:
        smtpAccount = view.findUUID(uuid)

        if smtpAccount is not None:
            for acc in smtpAccount.accounts:
                if acc.isActive or includeInactives:
                    if acc.host and acc.username and \
                       hasattr(acc, 'replyToAddress'):
                        replyToAddress = acc.replyToAddress
                        break

        return (smtpAccount, replyToAddress)

    """
    Get the default Mail Account
    """
    parentAccount = schema.ns('osaf.pim', view).currentMailAccount.item

    if parentAccount is not None:
        if hasattr(parentAccount, 'replyToAddress'):
            replyToAddress = parentAccount.replyToAddress

        """
        Get the default SMTP Account
        """
        try:
            smtpAccount = parentAccount.defaultSMTPAccount

        except ItemError.NoValueForAttributeError:
            pass

    return(smtpAccount, replyToAddress)


def getCurrentMailAccount(view, uuid=None):
    """
    This function returns either an C{IMAPAccount} or C{POPAccount} in the
    Repository. If uuid is not None will try and retrieve the account that
    has the uuid passed.  Otherwise the method will try and retrieve the
    current C{IMAPAccount} or C{POPAccount}.

    @param uuid: The C{uuid} of the account.
                 If no C{uuid} passed will return the current account
    @type uuid: C{uuid}
    @return C{IMAPAccount} or C{POPAccount}
    """

    if uuid is not None:
        account = view.findUUID(uuid)

    else:
        account = schema.ns('osaf.pim', view).currentMailAccount.item

    return account

class connectionSecurityEnum(schema.Enumeration):
    values = "NONE", "TLS", "SSL"


class AccountBase(items.ContentItem):

    schema.kindInfo(
        description="The base kind for various account kinds, such as "
                    "IMAP, SMTP, WebDav"
    )

    numRetries = schema.One(
        schema.Integer,
        doc = 'How many times to retry before giving up',
        initialValue = 0,
    )
    username = schema.One(
        schema.Text,
        doc = 'The account login name',
        initialValue = u'',
    )
    password = schema.One(
        schema.Text,
        doc = 'This could either be a password or some other sort of '
              'authentication info. We can use it for whatever is needed '
              'for this account type.\n\n'
            'Issues:\n'
            '   This should not be a simple string. We need some solution for '
            'encrypting it.\n',
        initialValue = u'',
    )
    host = schema.One(
        schema.Text,
        doc = 'The hostname of the account',
        initialValue = u'',
    )
    port = schema.One(
        schema.Integer, doc = 'The port number to use',
    )
    connectionSecurity = schema.One(
        connectionSecurityEnum,
        doc = 'The security mechanism to leverage for a network connection',
        initialValue = 'NONE',
    )
    pollingFrequency = schema.One(
        schema.Integer,
        doc = 'Frequency in seconds',
        initialValue = 300,
    )
    mailMessages = schema.Sequence(
        doc = 'Mail Messages sent or retrieved with this account ',
        initialValue = [],
    ) # inverse of MailStamp.parentAccount

    timeout = schema.One(
        schema.Integer,
        doc = 'The number of seconds before timing out a stalled connection',
        initialValue = 20,
    )

    isActive = schema.One(
        schema.Boolean,
        doc = 'Whether or not an account should be used for sending or '
              'fetching email',
        initialValue = True,
    )

    @classmethod
    def getActiveAccounts(cls, view):
        for item in cls.iterItems(view):
            if item.isActive and item.host and item.username:
                yield item


class DownloadAccountBase(AccountBase):

    schema.kindInfo(
        description="Base Account for protocols that download mail",
    )

    defaultSMTPAccount = schema.One(
        doc = 'Which SMTP account to use for sending mail from this account',
        initialValue = None,
    ) # inverse of SMTPAccount.accounts

    downloadMax = schema.One(
        schema.Integer,
        doc = 'The maximum number of messages to download before forcing a repository commit',
        initialValue = 6,
    )

    replyToAddress = schema.One(
        initialValue = None
    ) # inverse of EmailAddress.accounts

    @apply
    def emailAddress():
        def fget(self):
            return self.replyToAddress.emailAddress
        def fset(self, value):
            self.replyToAddress.emailAddress = value
        return property(fget, fset)

    @apply
    def fullName():
        def fget(self):
            return self.replyToAddress.fullName
        def fset(self, value):
            self.replyToAddress.fullName = value
        return property(fget, fset)

    @schema.observer(replyToAddress)
    def onReplyToAddressChange(self, op, name):
        emailAddress = getattr(self, 'emailAddress', None)

        if emailAddress and EmailAddress.isValidEmailAddress(emailAddress):
            meAddressCollection = schema.ns("osaf.pim", self.itsView).meAddressCollection

            addr = EmailAddress.findEmailAddress(self.itsView, emailAddress, meAddressCollection)

            if addr is None:
                meAddressCollection.append(self.replyToAddress)

                for item in self.replyToAddress.messagesFrom:
                    checkIfFromMe(MailStamp(item), 0)

                for item in self.replyToAddress.messagesReplyTo:
                    checkIfFromMe(MailStamp(item), 1)

                for item in self.replyToAddress.messagesTo:
                    checkIfToMe(MailStamp(item), 0)

                for item in self.replyToAddress.messagesCc:
                    checkIfToMe(MailStamp(item), 1)


class SMTPAccount(AccountBase):

    accountType = "SMTP"

    schema.kindInfo(
        description="An SMTP Account",
    )

    fromAddress = schema.One(
        initialValue = None
    )

    @apply
    def emailAddress():
        def fget(self):
            return self.fromAddress.emailAddress
        def fset(self, value):
            self.fromAddress.emailAddress = value
        return property(fget, fset)

    port = schema.One(
        schema.Integer,
        doc = 'The non-SSL port number to use\n\n'
            "Issues:\n"
            "   In order to get a custom initialValue for this attribute for an "
            "SMTPAccount, I defined a 'duplicate' attribute, also named "
            "'port', which normally would have been inherited from AccountBase\n",
        initialValue = 25,
    )

    useAuth = schema.One(
        schema.Boolean,
        doc = 'Whether or not to use authentication when sending mail',
        initialValue = False,
    )

    accounts = schema.Sequence(
        DownloadAccountBase,
        doc = 'Which accounts use this SMTP account as their default',
        initialValue = [],
        inverse = DownloadAccountBase.defaultSMTPAccount,
    )

    messageQueue = schema.Sequence(
        doc = "The Queue of mail messages  to be sent from this account. "
              "Used primarily for offline mode.",
        initialValue = [],
    )

    #Commented out for Preview
    #signature = schema.One(
    #    schema.Text,
    #    description =
    #        "Issues:\n"
    #        '   Basic signiture addition to an outgoing message will be refined '
    #        'in future releases\n',
    #)

    @classmethod
    def getActiveAccounts(cls, view):
        for item in cls.iterItems(view):
            if item.isActive and item.host:
                yield item

    @schema.observer(fromAddress)
    def onFromAddressChange(self, op, name):
        emailAddress = getattr(self, 'emailAddress', None)

        if emailAddress and EmailAddress.isValidEmailAddress(emailAddress):
            meAddressCollection = schema.ns("osaf.pim", self.itsView).meAddressCollection

            addr = EmailAddress.findEmailAddress(self.itsView, emailAddress, meAddressCollection)

            if addr is None:
                meAddressCollection.append(self.fromAddress)

                for item in self.fromAddress.messagesFrom:
                    checkIfFromMe(MailStamp(item), 0)

                for item in self.fromAddress.messagesReplyTo:
                    checkIfFromMe(MailStamp(item), 1)

                for item in self.fromAddress.messagesTo:
                    checkIfToMe(MailStamp(item), 0)

                for item in self.fromAddress.messagesCc:
                    checkIfToMe(MailStamp(item), 1)

                self.itsView.commit()

class IMAPAccount(DownloadAccountBase):

    accountType = "IMAP"

    schema.kindInfo(
        description = "An IMAP Account",
    )

    port = schema.One(
        schema.Integer,
        doc = 'The non-SSL port number to use\n\n'
            "Issues:\n"
            "   In order to get a custom initialValue for this attribute for "
            "an IMAPAccount, I defined a 'duplicate' attribute, also named "
            "'port', which normally would have been inherited from AccountBase\n",
        initialValue = 143,
    )

    #This is contains the last downloaded IMAP Message UID
    messageDownloadSequence = schema.One(
        schema.Integer,
        initialValue = 0,
    )


class POPAccount(DownloadAccountBase):

    accountType = "POP"

    schema.kindInfo(
        description = "A POP Account",
    )

    port = schema.One(
        schema.Integer,
        doc = 'The non-SSL port number to use\n\n'
            "Issues:\n"
            "   In order to get a custom initialValue for this attribute for "
            "a POPAccount, I defined a 'duplicate' attribute, also named "
            "'port', which normally would have been inherited from AccountBase\n",
        initialValue = 110,
    )

    downloadedMessageUIDS = schema.Mapping(
        schema.Text,
        doc = 'Used for quick look up to discover if a message has already been downloaded',
        initialValue = {},
    )

    leaveOnServer = schema.One(
        schema.Boolean,
        doc = 'Whether or not to leave messages on the server after downloading',
        initialValue = True,
    )


class MailDeliveryError(items.ContentItem):

    schema.kindInfo(
        description=
            "Contains the error data associated with a MailDelivery Type"
    )

    errorCode = schema.One(
        schema.Integer,
        doc = 'The Error Code returned by the Delivery Transport',
        initialValue = 0,
    )

    errorString = schema.One(schema.Text, initialValue = u'')

    errorDate = schema.One(schema.DateTime)

    mailDelivery = schema.One(
        doc = 'The Mail Delivery that cause this error',
        initialValue = None
    ) # inverse of MailDeliveryBase.deliveryErrors


class MailDeliveryBase(items.ContentItem):
    schema.kindInfo(
        description =
            "Parent kind for delivery-specific attributes of a MailMessage"
    )

    mailMessage = schema.One(
        doc = 'Message which this delivery item refers to',
        initialValue = None,
    ) # inverse MailStamp.deliveryExtension

    deliveryErrors = schema.Sequence(
        MailDeliveryError,
        doc = 'Mail Delivery Errors associated with this transport',
        initialValue = [],
        inverse = MailDeliveryError.mailDelivery,
    )

#Commented out for preview
#class historyEnum(schema.Enumeration):
#    values = "QUEUED", "FAILED", "SENT"

class stateEnum(schema.Enumeration):
    values = "DRAFT", "QUEUED", "SENT", "FAILED"


class SMTPDelivery(MailDeliveryBase):

    schema.kindInfo(
        description = "Tracks the status of an outgoing message\n\n"
            "Issues:\n\n"
            "   Currently the parcel loader can't set a default value for the "
            "state attribute\n",
    )

    #Commented out for preview
    #history = schema.Sequence(
    #    historyEnum,
    #    initialValue = [],
    #)
    #tries = schema.One(
    #    schema.Integer,
    #    doc = 'How many times we have tried to send it',
    #    initialValue = 0,
    #)

    state = schema.One(
        stateEnum,
        doc = 'The current state of the message\n\n',
        initialValue = "DRAFT",
    )

    def sendFailed(self):
        """
        Called from the Twisted thread to log errors in Send.
        """
        #Commented out for preview
        #self.history.append("FAILED")
        #self.tries += 1
        self.state = "FAILED"


    def sendSucceeded(self):
        """
        Called from the Twisted thread to log successes in Send.
        """
        #self.history.append("SENT")
        #self.tries += 1
        self.state = "SENT"


class IMAPDelivery(MailDeliveryBase):

    schema.kindInfo(
        description = "Tracks the state of an inbound message",
    )

    #XXX Reference back to the folder object
    #the message came from on IMAP Server
    folder = schema.One(
        schema.Text, initialValue = u'',
    )

    uid = schema.One(
        schema.Long,
        doc = 'The unique IMAP ID for the message',
        initialValue = 0L,
    )

    #Commented out for Preview
    #namespace = schema.One(
    #    schema.Text,
    #    doc = 'The namespace of the message',
    #    initialValue = u'',
    #)

    #Commented out for Preview
    #flags = schema.Sequence(
    #    schema.Text, initialValue = [],
    #)


class POPDelivery(MailDeliveryBase):

    schema.kindInfo(
        description = "Tracks the state of an inbound message",
    )

    #XXX Do pop messages have a UID? Why is it text and not a long
    uid = schema.One(
        schema.Text,
        doc = 'The unique POP ID for the message',
        initialValue = '',
    )


class MIMEBase(items.ContentItem):
    """Superclass for the various MIME classes"""
    mimeType = schema.One(schema.Text, initialValue = '')

    mimeContainer = schema.One(
        initialValue = None
    ) # inverse of MIMEContainer.mimeParts

    schema.addClouds(
        sharing = schema.Cloud(literal = [mimeType]),
    )


class MIMENote(MIMEBase):
    # @@@MOR This used to subclass notes.Note also, but since that superKind
    # was removed from MIMENote's superKinds list
    """MIMEBase and Note, rolled into one"""

    filename = schema.One(
        schema.Text, initialValue = u'',
    )
    filesize = schema.One(schema.Long)

    schema.addClouds(
        sharing = schema.Cloud(literal = [filename, filesize]),
    )


class MIMEContainer(MIMEBase):
    mimeParts = schema.Sequence(
        MIMEBase,
        initialValue = [],
        inverse = MIMEBase.mimeContainer,
    )

    schema.addClouds(
        sharing = schema.Cloud(
            byValue = [mimeParts]
        )
    )


class MailStamp(stamping.Stamp):
    """

    MailStamp is the bag of Message-specific attributes.

    Used to stamp a content item with mail message attributes.

    Issues:
      - Once we have attributes and a cloud defined for Attachment,
        we need to include attachments by cloud, and not by value.
      - Really not sure what to do with the 'downloadAccount' attribute
        and how it should be included in the cloud.  For now it's byValue.
      - The modelling of the various subclasses of MIMEBase as Annotations
        seems artificial. Note, however, that you can't inherit from both
        Item and Annotation, so this seemed like the way to go.
    """

    schema.kindInfo(annotates = notes.Note)
    __use_collection__ = True

    mimeContent = schema.One(
        MIMEContainer,
        defaultValue=None,
    )

    deliveryExtension = schema.One(
        MailDeliveryBase,
        initialValue = None,
        inverse = MailDeliveryBase.mailMessage,
    )

    isOutbound = schema.One(schema.Boolean, initialValue = False)

    parentAccount = schema.One(
        AccountBase, initialValue = None, inverse = AccountBase.mailMessages,
    )
    #Commented out for Preview
    #spamScore = schema.One(schema.Float, initialValue = 0.0)
    rfc2822Message = schema.One(schema.Lob, indexed=False)

    dateSentString = schema.One(schema.Text, initialValue = '')
    dateSent = schema.One(schema.DateTimeTZ, indexed=True)
    messageId = schema.One(schema.Text, initialValue = '')

    # inverse of EmailAddress.messagesTo
    toAddress = schema.Sequence(
        initialValue = [],
    )

    # inverse of EmailAddress.messagesFrom
    fromAddress = schema.One(
        initialValue = None,
    )
    # inverse of EmailAddress.messagesReplyTo
    replyToAddress = schema.One(initialValue = None)

    # inverse of EmailAddress.messagesBcc
    bccAddress = schema.Sequence(initialValue = [])

    # inverse of EmailAddress.messagesCc
    ccAddress = schema.Sequence(initialValue = [])

    @apply
    def subject():
        def fget(self):
            return self.itsItem.displayName
        def fset(self, value):
            self.itsItem.displayName = value
        return schema.Calculated(schema.Text, (items.ContentItem.displayName,),
                                 fget, fset)

    @apply
    def body():
        def fget(self):
            return self.itsItem.body
        def fset(self, value):
            self.itsItem.body = value
        return schema.Calculated(schema.Text, (items.ContentItem.body,),
                                 fget, fset)

    inReplyTo = schema.One(schema.Text, indexed=False)

    referencesMID = schema.Sequence(schema.Text, initialValue = [])

    headers = schema.Mapping(
        schema.Text, doc = 'Catch-all for headers', initialValue = {},
    )

    chandlerHeaders = schema.Mapping(schema.Text, initialValue = {})

    fromMe = schema.One(schema.Boolean, initialValue=False, doc = "Boolean flag used to signal that the MailStamp instance contains a from or reply to address that matches one or more of the me addresses")

    toMe = schema.One(schema.Boolean, initialValue=False, doc = "boolean flag used to signal that the MailStamp instance contains a to or cc address that matches one or more of the me addresses")

    @schema.observer(fromAddress, replyToAddress)
    def onFromMeChange(self, op, name):
        if op != "set":
            return

        if name.endswith("fromAddress"):
            checkIfFromMe(self, 0)
        else:
            checkIfFromMe(self, 1)

    @schema.observer(toAddress, ccAddress)
    def onToMeChange(self, op, name):
        if op != "set":
            return

        if name.endswith("toAddress"):
            checkIfToMe(self, 0)
        else:
            checkIfToMe(self, 1)

    @schema.observer(toAddress, isOutbound, stamping.Stamp.stamp_types)
    def onAddressChange(self, op, name):
        self.itsItem.updateDisplayWho(op, name)

    def addDisplayWhos(self, whos):
        # @@@ This code doesn't choose the right 'who' yet, but has enough
        # context to make the decision here. (If the decision depends
        # on more attributes, be sure to add them to the schema.observer list
        # on onAddressChange)
        if getattr(self, 'toAddress', None) is not None:
            toText = u", ".join(unicode(x) for x in self.toAddress)
            if len(toText) > 0:
                toPriority = self.isOutbound and 1 or 2
                whos.append((toPriority, toText, 'to'))
        if getattr(self, 'fromAddress', None) is not None:
            fromText = unicode(self.fromAddress)
            if len(fromText) > 0:
                fromPriority = self.isOutbound and 2 or 1
                whos.append((fromPriority, fromText, 'from'))

    schema.addClouds(
        sharing = schema.Cloud(
            byValue = [fromAddress, toAddress, dateSent,
                       ccAddress, bccAddress, replyToAddress],
        ),
        copying = schema.Cloud(
            mimeContent, dateSent,
            fromAddress, toAddress, ccAddress, bccAddress, replyToAddress,
        ),
    )

    def InitOutgoingAttributes(self):
        """
        Init any attributes on ourself that are appropriate for
        a new outgoing item.
        """
        self.isOutbound = True
        self.itsItem.InitOutgoingAttributes()

    # [Bug 6815] Because of schema loading issues, not all
    # MailStamp's inherited attributes' initialValues are available
    # at the time the Welcome Note is set up. For 0.7alpha4, we
    # just cache them here, and set them up in MailStamp.add().
    # Post-alpha4, this will be revisited, probably by making
    # MIMEBase derived from ContentItem again.
    EXTRA_INITIAL_VALUES = {}
    for cls in MIMEContainer, MIMEBase:
        for name, ob in cls.__dict__.iteritems():
            try:
                EXTRA_INITIAL_VALUES[name] = ob.cdesc.initialValue
            except AttributeError:
                pass


    def add(self):
        """
        Init only the attributes specific to this mixin.
        Called when stamping adds these attributes, and from __init__ above.
        """

        super(MailStamp, self).add()

        if getattr(self, 'mimeContent', None) is None:
            self.mimeContent = MIMEContainer(itsView=self.itsItem.itsView,
                                               mimeType='message/rfc822')
        # default the fromAddress to "me"
        if getattr(self, 'fromAddress', None) is None:
            self.fromAddress = EmailAddress.getCurrentMeEmailAddress(self.itsItem.itsView)
        for name, value in self.EXTRA_INITIAL_VALUES.iteritems():
            if not hasattr(self, name):
                setattr(self, name, value)

    @schema.observer(dateSent)
    def onDateSentChanged(self, op, name):
        self.itsItem.updateDisplayDate(op, name)

    def addDisplayDates(self, dates):
        dateSent = getattr(self, 'dateSent', None)
        if dateSent is not None:
            dates.append((dateSent, 'dateSent'))

    def outgoingMessage(self, account, type='SMTP'):
        assert type == "SMTP", "Only SMTP currently supported"

        assert isinstance(account, SMTPAccount)

        if self.deliveryExtension is None:
            self.deliveryExtension = SMTPDelivery(itsView=self.itsItem.itsView)

        self.isOutbound = True
        self.parentAccount = account

    def incomingMessage(self, account, type="IMAP"):
        assert isinstance(account, DownloadAccountBase)

        view = self.itsItem.itsView

        if self.deliveryExtension is None:
            if type == "IMAP":
                 self.deliveryExtension = IMAPDelivery(itsView=view)
            elif type == "POP":
                 self.deliveryExtension = POPDelivery(itsView=view)

        self.isOutbound = False
        self.parentAccount = account

        #Add to the dashboard
        schema.ns('osaf.pim', view).allCollection.add(self.itsItem)
        self.itsItem.mine = True


    def getAttachments(self):
        """
        First pass at API will be expanded upon later.
        """
        content = self.mimeContent # Never raises b/c defaultValue
        if content is None:
            return []
        else:
            return list(content.mimeParts or [])

    def getNumberOfAttachments(self):
        """
        First pass at API will be expanded upon later.
        """
        return len(self.getAttachments())

    def getSendability(self, ignoreAttr=None):
        """
        Return whether this item is ready to send: 'sendable', 'sent',
        or 'not'. if ignoreAttr is specified, don't verify that value
        (because it's being edited in the UI and is known to be valid,
        and will get saved before sending).
        """
        # Not outbound?
        if not self.isOutbound:
            return 'not'

        # Already sent?
        try:
            sent = self.deliveryExtension.state == "SENT"
        except AttributeError:
            sent = False
        if sent:
            return 'sent'

        # Addressed?
        # (This test will get more complicated when we add cc, bcc, etc.)
        sendable = ((ignoreAttr == 'toAddress' or len(self.toAddress) > 0) and
                    (ignoreAttr == 'fromAddress' or self.fromAddress is not None))
        return sendable and 'sendable' or 'not'


def MailMessage(*args, **keywds):
    """Return a newly created Note, stamped with MailStamp."""
    note = notes.Note(*args, **keywds)
    message = MailStamp(note)

    message.add()
    return message


class MIMEBinary(MIMENote):
    data = schema.One(schema.Lob, indexed=False)


class MIMEText(MIMENote):

    charset = schema.One(
        schema.Text,
        initialValue = 'utf-8',
    )
    lang = schema.One(
        schema.Text,
        initialValue = 'en',
    )

    data = schema.One(schema.Text, indexed=False)

class MIMESecurity(MIMEContainer):
    pass

class CollectionInvitation(schema.Annotation):
    schema.kindInfo(annotates = collections.ContentCollection)

    invitees = schema.Sequence(
        doc="The people who are being invited to share in this item; filled "
        "in when the user types in the DV's 'invite' box, then cleared on "
        "send (entries copied to the share object).\n\n"
        "Issue: Bad that we have just one of these per item collection, "
        "though an item collection could have multiple shares post-0.5",
        initialValue=()
    ) # inverse of EmailAddress



class EmailAddress(items.ContentItem):
    """An item that represents a simple email address, plus
all the info we might want to associate with it, like
lists of message to and from this address.

Example: abe@osafoundation.org

Issues:
   Someday we might want to have other attributes.  One example
   might be an 'is operational' flag that tells whether this
   address is still in service, or whether mail to this has been
   bouncing lately. Another example might be a 'superseded by'
   attribute, which would point to another Email Address item.

"""
    emailAddress = schema.One(
        schema.Text,
        doc = 'The email address.\n\n'
            "Examples:\n"
            '   "abe@osafoundation.org"\n',
        indexed = True,
        initialValue = u'',
    )
    fullName = schema.One(
        schema.Text,
        doc = 'A first and last name associated with this email address',
        indexed = True,
        initialValue = u'',
    )

    #vcardType = schema.One(
    #    schema.Text,
    #    doc = "Typical vCard types are values like 'internet', 'x400', and "
    #          "'pref'. Chandler will use this attribute when doing "
    #          "import/export of Contact records in vCard format.",
    #    initialValue = u'',
    #)

    accounts = schema.Sequence(
        DownloadAccountBase,
        doc = 'A list of Email Accounts that use this Email Address as the '
              'reply address for mail sent from the account.',
        initialValue = [],
        inverse = DownloadAccountBase.replyToAddress,
    )

    messagesBcc = schema.Sequence(
        MailStamp,
        doc = 'A list of messages with their Bcc: header referring to this address',
        initialValue = [],
        inverse = MailStamp.bccAddress,
    )

    messagesCc = schema.Sequence(
        MailStamp,
        doc = 'A list of messages with their cc: header referring to this address',
        initialValue = [],
        inverse = MailStamp.ccAddress,
    )

    messagesFrom = schema.Sequence(
        MailStamp,
        doc = 'A list of messages with their From: header referring to this address',
        initialValue = [],
        inverse = MailStamp.fromAddress,
    )

    messagesReplyTo = schema.Sequence(
        MailStamp,
        doc = 'A list of messages with their Reply-To: header referring to this address',
        initialValue = [],
        inverse = MailStamp.replyToAddress,
    )

    messagesTo = schema.Sequence(
        MailStamp,
        doc = 'A list of messages with their To: header referring to this address',
        initialValue = [],
        inverse = MailStamp.toAddress,
    )

    inviteeOf = schema.Sequence(
        collections.ContentCollection,
        doc = 'List of collections that the user is about to be invited to share with.',
        inverse = CollectionInvitation.invitees,
    )

    schema.addClouds(
        sharing = schema.Cloud(literal = [emailAddress, fullName])
    )

    def __init__(self, itsName=None, itsParent=None, itsKind=None,
        itsView=None, clone=None, **kw
    ):
        super(EmailAddress, self).__init__(
            itsName, itsParent, itsKind, itsView, **kw
        )

        # copy the attributes if a clone was supplied
        if clone is not None:
            try:
                self.emailAddress = clone.emailAddress[:]
            except AttributeError:
                pass
            try:
                self.fullName = clone.fullName[:]
            except AttributeError:
                pass

    def __str__(self):
        if self.isStale():
            return super(EmailAddress, self).__str__()

        return self.__unicode__().encode('utf8')

    def __unicode__(self):
        """
        User readable string version of this address.
        """
        if self.isStale():
            return super(EmailAddress, self).__unicode__()
            # Stale items shouldn't go through the code below

        fullName = getattr(self, 'fullName', u'')
        if len(fullName) > 0:
            if self.emailAddress:
                return fullName + u' <' + self.emailAddress + u'>'
            else:
                return fullName
        elif self is self.getCurrentMeEmailAddress(self.itsView):
            return messages.ME
        else:
            return unicode(getattr(self, 'emailAddress', self.itsName) or
                           self.itsUUID.str64())

        """
        Factory Methods
        --------------
        When creating a new EmailAddress, we check for an existing item first.
        We do look them up in the repository to prevent duplicates, but there's
        nothing to keep bad ones from accumulating, although repository
        garbage collection should eventually remove them.

        The "me" entity is used for Items created by the user, and it
        gets a reasonable emailaddress filled in when a send is done.

        For performant operations use theEmailAddress.findEmailAddress method
        which leverages an index.
        """

    @classmethod
    def getEmailAddress(cls, view, nameOrAddressString, fullName=''):
        """
        Lookup or create an EmailAddress based on the supplied string.

        If a matching EmailAddress object is found in the repository, it
        is returned.  If there is no match, then a new item is created
        and returned.

        There are two ways to call this method:
          1. with something the user typed in nameOrAddressString, which
             will be parsed, and no fullName is needed
          2. with an plain email address in the nameOrAddressString, and a
             full name in the fullName field

        If a match is found for both name and address then it will be used.

        If there is no name specified, a match on address will be returned.

        If there is no address specified, a match on name will be returned.

        If both name and address are specified, but there's no entry that
        matches both, then a new entry is created.

        @param nameOrAddressString: emailAddress string, or fullName for lookup,
        or both in the form "name <address>"
        @type nameOrAddressString: C{unicode}
        @param fullName: optional explict fullName when not using the
        "name <address>" form of the nameOrAddressString parameter
        @type fullName: C{unicode}

        @return: C{EmailAddress} or None if not found, and nameOrAddressString is\
        not a valid email address.
        """
        # @@@DLD remove when we better sort out creation of "me" address w/o an account setup
        if nameOrAddressString is None:
            nameOrAddressString = u''

        # strip the address string of whitespace and question marks
        address = nameOrAddressString.strip ().strip(u'?')

        # check for "me"
        if address == messages.ME:
            return cls.getCurrentMeEmailAddress(view)

        # if no fullName specified, parse apart the name and address if we can
        if fullName != u'':
            name = fullName
        else:
            try:
                address.index(u'<')
            except ValueError:
                name = address
            else:
                name, address = address.split(u'<')
                address = address.strip(u'>').strip()
                name = name.strip()
                # ignore a name of "me"
                if name == messages.ME:
                    name = u''

        # check if the address looks like a valid emailAddress
        isValidAddress = cls.isValidEmailAddress(address)
        if not isValidAddress:
            address = None

        """
        At this point we should have:
            name - the name to search for, or ''
            address - the address to search for, or None
        If the user specified a single word which could also be a valid
        email address, we could have that word in both the address and
        name variables.
        """
        # @@@DLD - switch on the better queries
        # Need to override compare operators to use emailAddressesAreEqual,
        #  deal with name=='' cases, name case sensitivity, etc

        addresses = []
        for candidate in EmailAddress.iterItems(view):
            if isValidAddress:
                if cls.emailAddressesAreEqual(candidate.emailAddress, address):
                    # found an existing address!
                    addresses.append(candidate)
            elif name != u'' and name == candidate.fullName:
                # full name match
                addresses.append(candidate)

        # process the result(s)
        # Hope for a match of both name and address
        # fall back on a match of the address, then name
        addressMatch = None
        nameMatch = None
        for candidate in addresses:
            if isValidAddress:
                if cls.emailAddressesAreEqual(candidate.emailAddress, address):
                    # found an existing address match
                    addressMatch = candidate
            if name != u'' and name == candidate.fullName:
                # full name match
                nameMatch = candidate
                if addressMatch is not None:
                    # matched both
                    return addressMatch
        else:
            # no double-matches found
            if name == address:
                name = u''
            if addressMatch is not None and name == u'':
                return addressMatch
            if nameMatch is not None and address is None:
                return nameMatch
            if isValidAddress:
                # make a new EmailAddress
                if address is None:
                    address = u""
                if name is None:
                    name = u""
                newAddress = EmailAddress(itsView=view,
                                          emailAddress=address,
                                          fullName=name)
                return newAddress
            else:
                return None

    def _compareAddr(self, other):
        return cmp(self.emailAddress.lower(), other.emailAddress.lower())

    def _compareFullName(self, other):
        return cmp(self.fullName.lower(), other.fullName.lower())

    @classmethod
    def findEmailAddress(cls, view, emailAddress, collection=None):
        """
        Find a single EmailAddress that exactly matches this one.
        """

        if collection is None:
            collection = schema.ns("osaf.pim", view).emailAddressCollection

        emailAddress = emailAddress.lower()

        def compareAddr(uuid):
            return cmp(emailAddress,
                       view.findValue(uuid, 'emailAddress').lower())

        uuid = collection.findInIndex('emailAddress', 'exact', compareAddr)
        if uuid is None:
            return None

        return view[uuid]

    @classmethod
    def generateMatchingEmailAddresses(cls, view, partialAddress):
        """
        Generate any EmailAddresses whose emailAddress or fullName starts
        with this.
        """
        collection = schema.ns("osaf.pim", view).emailAddressCollection
        partialAddress = unicode(partialAddress).lower()
        for indexName in ('emailAddress', 'fullName'):
            def _compare(uuid):
                attrValue = view.findValue(uuid, indexName).lower()
                if attrValue.startswith(partialAddress):
                    return 0
                return cmp(partialAddress, attrValue)
            firstUUID = collection.findInIndex(indexName, 'first', _compare)

            if firstUUID is None:
                continue

            lastUUID = collection.findInIndex(indexName, 'last', _compare)
            for uuid in collection.iterindexkeys(indexName, firstUUID, lastUUID):
                match = view[uuid]
                if unicode(match).lower() != partialAddress:
                    yield match

    @classmethod
    def format(cls, emailAddress, encode=False):
        assert isinstance(emailAddress, EmailAddress)

        if emailAddress.fullName is not None and \
           len(emailAddress.fullName.strip()) > 0:
            if encode:
                from email.Header import Header
                return Header(emailAddress.fullName).encode() + u" <" + \
                              emailAddress.emailAddress + u">"
            else:
                return emailAddress.fullName + u" <" + emailAddress.emailAddress + u">"

        return emailAddress.emailAddress

    @classmethod
    def isValidEmailAddress(cls, emailAddress):
        """
        This method tests an email address for valid syntax as defined RFC 822.
        The method validates addresses in the form 'John Jones <john@test.com>'
        and 'john@test.com'

        @param emailAddress: A string containing a email address to validate.
        @type emailAddress: C{String}
        @return: C{Boolean}
        """

        assert isinstance(emailAddress, (str, unicode))

        emailAddress = Utils.parseaddr(emailAddress)[1]

        return re.match("^(([^<>()[\]\\.,;:\s@\"]+(\.[^<>()[\]\\.,;:\s@\"]+)*)|(\".+\"))@((\[[0-9]{1,3}\.[0-9]{1,3}\.[0-9]{1,3}\.[0-9]{1,3}\])|(([a-zA-Z\-0-9]+\.)+[a-zA-Z]{2,}))$", emailAddress) is not None

    @classmethod
    def parseEmailAddresses(cls, view, addressesString):
        """
        Parse the email addresses in addressesString and return
        a tuple with: (the processed string, a list of EmailAddress
        items created/found for those addresses, the number of
        invalid addresses we found).
        """
        # If we got nothing or whitespace, return it as-is.
        if len(addressesString.strip()) == 0:
            return (addressesString, [], 0)

        validAddresses = []
        processedAddresses = []
        invalidCount = 0

        # get the user's address strings into a list; tolerate
        # commas or semicolons as separators
        addresses = [ address.strip() for address in \
                      addressesString.replace('?','').replace(';', ',').split(',') ]

        # build a list of all processed addresses, and all valid addresses
        for address in addresses:
            ea = EmailAddress.getEmailAddress(view, address)
            if ea is None:
                processedAddresses.append(address + '?')
                invalidCount += 1
            else:
                processedAddresses.append(unicode(ea))
                validAddresses.append(ea)

        # prepare the processed addresses return value
        processedResultString = ', '.join (processedAddresses)
        return (processedResultString, validAddresses, invalidCount)

    @classmethod
    def emailAddressesAreEqual(cls, emailAddressOne, emailAddressTwo):
        """
        This method tests whether two email addresses are the same.
        Addresses can be in the form john@jones.com or John Jones <john@jones.com>.

        The method strips off the username and <> brakets if they exist and
        just compares the actual email addresses for equality. It will not
        look to see if each address is RFC 822 compliant only that the strings
        match. Use C{EmailAddress.isValidEmailAddress} to test for validity.

        @param emailAddressOne: A string containing a email address to compare.
        @type emailAddressOne: C{String}
        @param emailAddressTwo: A string containing a email address to compare.
        @type emailAddressTwo: C{String}
        @return: C{Boolean}
        """
        assert isinstance(emailAddressOne, (str, unicode))
        assert isinstance(emailAddressTwo, (str, unicode))

        emailAddressOne = Utils.parseaddr(emailAddressOne)[1]
        emailAddressTwo = Utils.parseaddr(emailAddressTwo)[1]

        return emailAddressOne.lower() == emailAddressTwo.lower()


    @classmethod
    def getCurrentMeEmailAddress(cls, view):
        """
        Lookup the "me" EmailAddress.
        The "me" EmailAddress is whichever entry is the current IMAP default
        address.
        """

        # See if an IMAP/POP account is configured:
        account = getCurrentMailAccount(view)
        if account is None or not account.replyToAddress or not \
           account.replyToAddress.emailAddress:
            # No IMAP/POP set up, so check SMTP:
            account, replyTo = getCurrentSMTPAccount(view)
            if account is None or not account.fromAddress or not \
               account.fromAddress.emailAddress:
                return None
            else:
                return account.fromAddress
        else:
            return account.replyToAddress


# Map from account type strings to account types

ACCOUNT_TYPES = {
    'POP': POPAccount,
    'SMTP': SMTPAccount,
    'IMAP': IMAPAccount,
}


class CommunicationStatus(schema.Annotation):
    """
    Generate a value that expresses the communications status of an item, 
    such that the values can be compared for indexing for the communications
    status column of the Dashboard.
    
    The sort terms are:
      1. unread, needs-reply, read
      2. Not mail (and no error), sent mail, error, queued mail, draft mail
      3a. If #2 is not mail: created, edited
      3b. If #2 is mail: out, in, other
      4b. If #2 is mail: firsttime, updated
    """
    schema.kindInfo(annotates=items.ContentItem)

    # These flag bits govern the sort position of each communications state:
    # Terms with set "1"s further left will sort earlier.
    # 1:
    # (unread has neither of these set)
    # NEEDS_REPLY =  1
    # READ        = 1

    # 2:
    # (non-mail has none of these set)
    # SENT        =      1
    # ERROR       =     1
    # QUEUED      =    1
    # DRAFT       =   1

    # 3a:
    # (created has this bit unset)
    # EDITED      =       1
        
    # 3b:
    # OUT         =          1
    # IN          =         1
    # NEITHER     =        1
    
    # 4b:
    # (firsttime has this bit unset)
    # UPDATE      =           1

    
    UPDATE, OUT, IN, NEITHER, EDITED, SENT, ERROR, QUEUED, DRAFT, NEEDS_REPLY, READ = (
        1<<n for n in xrange(11)
    )
    
    @staticmethod
    def getItemCommState(itemOrUUID, view=None):
        """ Given an item or a UUID, determine its communications state """

        if isinstance(itemOrUUID, UUID):
            uuid = itemOrUUID
            assert view is not None, "Need a view for the UUID case!"
        else:
            uuid = itemOrUUID.itsUUID
            view = itemOrUUID.itsView
        
        modifiedFlags, lastMod, stampTypes, fromMe, \
        toMe, needsReply, read, error = \
            view.findValues(uuid, *(CommunicationStatus.attributeValues))

        result = 0
        
        if MailStamp in stampTypes:
            # update
            if items.Modification.sent in modifiedFlags:
                result |= CommunicationStatus.UPDATE
    
            # in, out, neither
            if toMe:
                result |= CommunicationStatus.IN
            if fromMe:
                result |= CommunicationStatus.OUT
            elif not toMe:
                result |= CommunicationStatus.NEITHER
                
            # queued
            if items.Modification.queued in modifiedFlags:
                result |= CommunicationStatus.QUEUED
            # update
            if items.Modification.sent in modifiedFlags:
                result |= CommunicationStatus.UPDATE
            # sent
            if lastMod in (items.Modification.sent, items.Modification.updated):
                result |= CommunicationStatus.SENT
            # draft if it's not one of the above
            if  result & (CommunicationStatus.SENT | CommunicationStatus.QUEUED
                          | CommunicationStatus.UPDATE) == 0:
                result |= CommunicationStatus.DRAFT
        else:
            # edited
            if items.Modification.edited in modifiedFlags:
                result |= CommunicationStatus.EDITED
                
        # needsReply
        if needsReply:
            result |= CommunicationStatus.NEEDS_REPLY
            
        # read
        if read:
            result |= CommunicationStatus.READ
        
        # error
        if error:
            result |= CommunicationStatus.ERROR
    
        return result
    
    @staticmethod
    def dump(status):
        """ 
        For debugging (and helpful unit-test messages), explain our flags. 
        'status' can be a set of flags, an item, or an item UUID.
        """
        if not isinstance(status, int):
            status = CommunicationStatus.getItemCommState(status)
        if status == 0:
            return "(none)"
        result = [ flagName for flagName in ('UPDATE', 'OUT', 'IN', 
                                             'NEITHER', 'EDITED', 
                                             'SENT', 'QUEUED', 
                                             'DRAFT', 'NEEDS_REPLY', 
                                             'READ')
                   if status & getattr(CommunicationStatus, flagName)]
        return '+'.join(result)

    attributeValues = (
        (items.ContentItem.modifiedFlags, set()),
        (items.ContentItem.lastModification, None),
        (stamping.Stamp.stamp_types, set()),
        (MailStamp.fromMe, False),
        (MailStamp.toMe, False),
        (items.ContentItem.needsReply, False),
        (items.ContentItem.read, True),
        (items.ContentItem.error, None)
    )
    status = schema.Calculated(
        schema.Integer,
        basedOn=tuple(t[0] for t in attributeValues),
        fget=lambda self: self.getItemCommState(self.itsItem),
    )
    attributeValues = tuple((attr.name, val) for attr, val in attributeValues)

