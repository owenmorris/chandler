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


""" Contains constants shared across the Mail Domain (SMTP, IMAP4, POP3) """

#python imports
import version
from PyICU import ChoiceFormat

from i18n import ChandlerMessageFactory as _

CHANDLER_USERAGENT = "Chandler (%s)" % version.version
CHANDLER_HEADER_PREFIX = "X-Chandler-"

CHANDLER_MAIL_FOLDER = _(u"Chandler Mail")
CHANDLER_TASKS_FOLDER = _(u"Chandler Tasks")
CHANDLER_EVENTS_FOLDER = _(u"Chandler Events")

INVALID_EMAIL_ADDRESS = _(u"Email Address %(emailAddress)s is not valid")

# Generic mail protocol message strings
MAIL_GENERIC_ERROR = _(u"The following error was raised:\n\n\t%(errText)s")
MAIL_PROTOCOL_ERROR = _(u"The server '%(hostName)s' raised the following error:\n\n\t%(errText)s")
MAIL_PROTOCOL_SUCCESS = _(u"Connection to server '%(hostName)s' was successful.")
MAIL_PROTOCOL_REQUIRES_TLS = _(u"The Server only allows secure login. Please enable TLS or SSL.")
MAIL_PROTOCOL_OFFLINE = _(u"%(accountName)s: offline mode no operation was performed")
MAIL_PROTOCOL_CONNECTION = _(u"%(accountName)s: connecting to server %(serverDNSName)s")
MAIL_PROTOCOL_CONNECTION_ERROR = _(u"Unable to connect to server please try again later")
MAIL_PROTOCOL_TIMEOUT_ERROR = _(u"Communication with the Server timed out. Please try again later.")

# Translatable message strings for downloads (POP, IMAP)
DOWNLOAD_NO_MESSAGES = _(u"%(accountName)s: no new messages found")
DOWNLOAD_CHECK_MESSAGES = _(u"%(accountName)s: checking for new mail messages ...")

INBOX_LIST_ERROR = _(u"Unable to determine the 'Inbox' status on the IMAP Server")

# Translatable message strings for uploads(SMTP)
UPLOAD_BAD_REPLY_ADDRESS = _(u"The Reply-To Address %(emailAddress)s is not valid")
UPLOAD_FROM_REQUIRED = _(u"A From Address is required to send a Mail Message")
UPLOAD_TO_REQUIRED = _(u"A To Address is required to send an SMTP Mail Message")

UPLOAD_OFFLINE = _(u'%(accountName)s: Chandler Mail is offline, "%(subject)s" queued for sending')
UPLOAD_START = _(u'%(accountName)s: sending "%(subject)s"')
UPLOAD_SENT = _(u'%(accountName)s: "%(subject)s" sent')


# Translatable message strings for account testing
TEST_OFFLINE = _(u"Chandler Mail is currently offline.\nTo perform this action, Mail must be in online mode.")

#POP3 error messags
POP_UIDL_ERROR = _(u"The POP3 Server does not support the 'UIDL' command.\nThis command is required by Chandler.")


# ChoiceFormat messages
#==========================
DOWNLOAD_CHANDLER_MESSAGES = ChoiceFormat(_(u"1#%(accountName)s: %(numberTotal)s message downloaded to Chandler (New: %(numberNew)s, Updates: %(numberUpdates)s, Duplicates: %(numberDuplicates)s)|1<%(accountName)s: %(numberTotal)s messages downloaded to Chandler (New: %(numberNew)s, Updates: %(numberUpdates)s, Duplicates: %(numberDuplicates)s)"))

DOWNLOAD_START_MESSAGES = ChoiceFormat(_(u"1#%(accountName)s: downloading %(numberOfMessages)s message ...|1<%(accountName)s: downloading %(numberOfMessages)s messages ..."))

POP_SEARCH_STATUS = _(u"%(accountName)s: searching %(start)s - %(end)s of %(total)s messages for Chandler Mail")

IMAP_SEARCH_STATUS = _(u"%(accountName)s: searching %(start)s - %(end)s of %(total)s messages for Chandler Mail in your '%(folderDisplayName)s'")

IMAP_INBOX_MISSING = _(u"%(accountName)s is not configured correctly.\nThe account settings contain no Inbox folder.")

IMAP_COMMIT_MESSAGES = _(u"%(accountName)s: commiting %(start)s - %(end)s of %(total)s messages from '%(folderDisplayName)s'")

POP_COMMIT_MESSAGES = _(u"%(accountName)s: commiting %(start)s - %(end)s of %(total)s messages")

# Number of seconds to wait to timeout connection when downloading mail
TIMEOUT = 30

# Number of seconds to wait to timeout connection for account testing
TESTING_TIMEOUT = 10

# If set to True dumps MailMessage structure
# during parsing to the chandler.log.
# This will only work in debugging mode
# i.e. __debug__ == True
VERBOSE = False

# Flag to improve download performance by ignoring
# non-text attachments.
IGNORE_ATTACHMENTS = True

WAIT_FOR_COMMIT = False
NOOP_INTERVAL = 10

MAX_COMMIT = 500
MAILWORKER_PRUNE_SIZE = MAILSERVICE_PRUNE_SIZE = 500

# This flag will signal whether to print
# the communications between the client
# and server when __debug__ is True. 
# This is especially handy
# when the traffic is encrypted (SSL/TLS).
# Options:
#    0 - No output logged.
#    1 - Caches last 4 protocol communications and
#        print to the stdout if an error is raised.
#    2 - All protocol communications printed
#        to stdout. Any errors raised are logged
#        to the chandler.log for debugging purposes
#        instead of being displayed in an alert dialog.
DEBUG_CLIENT_SERVER = 0

# The maximum number of message UID's to
# include in an IMAP search for Chandler Headers.
MAX_IMAP_SEARCH_NUM = 350


# The maximum number of message UID's to
# scan on a POP server for Chandler Headers
# between status bar message refreshes.
MAX_POP_SEARCH_NUM = 50
