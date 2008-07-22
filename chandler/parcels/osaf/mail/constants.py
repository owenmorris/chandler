#   Copyright (c) 2005-2008 Open Source Applications Foundation
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

#XXX For 1.0 the Chandler IMAP Folders will not
#    be localized since there are potential issues
#    when switching languages. For information see
#    bug 11430.
CHANDLER_MAIL_FOLDER = u"Chandler Mail"
CHANDLER_STARRED_FOLDER = u"Chandler Starred"
CHANDLER_TASKS_FOLDER = u"Chandler Tasks"
CHANDLER_EVENTS_FOLDER = u"Chandler Events"

# The IMAP folders (besides INBOX) we currently use to sync with Chandler
CURRENT_IMAP_FOLDERS = (
    CHANDLER_MAIL_FOLDER,
    CHANDLER_STARRED_FOLDER,
    CHANDLER_EVENTS_FOLDER
)

# The (now obsolete) "Chandler Tasks" folder
ALL_IMAP_FOLDERS = CURRENT_IMAP_FOLDERS + (CHANDLER_TASKS_FOLDER,)

INVALID_EMAIL_ADDRESS = _(u"Email Address %(emailAddress)s is not valid.")

# Generic mail protocol message strings
MAIL_GENERIC_ERROR = _(u"Mail error:\n\n\t%(errText)s")
MAIL_PROTOCOL_ERROR = _(u"Error from mail server '%(hostName)s':\n\n\t%(errText)s")
MAIL_PROTOCOL_SUCCESS = _(u"Connection to server '%(hostName)s' was successful.")
MAIL_PROTOCOL_REQUIRES_TLS = _(u"The server requires secure login. Please enable TLS or SSL.")
MAIL_PROTOCOL_OFFLINE = _(u"%(accountName)s is offline. No operation was performed.")
MAIL_PROTOCOL_CONNECTION = _(u"%(accountName)s: Connecting to server %(serverDNSName)s...")
MAIL_PROTOCOL_CONNECTION_ERROR = _(u"Unable to connect to server. Please try again later.")
MAIL_PROTOCOL_TIMEOUT_ERROR = _(u"Connection to server timed out. Please try again later.")

# Translatable message strings for downloads (POP, IMAP)
DOWNLOAD_NO_MESSAGES = _(u"%(accountName)s: No new messages found.")
DOWNLOAD_CHECK_MESSAGES = _(u"%(accountName)s: Checking for new mail messages...")

INBOX_LIST_ERROR = _(u"Unable to determine status of Inbox on server.")

# Translatable message strings for uploads(SMTP)
UPLOAD_BAD_REPLY_ADDRESS = _(u"The Reply-to address %(emailAddress)s is not valid.")
UPLOAD_FROM_REQUIRED = _(u"A From: address is required to send this message.")
UPLOAD_TO_REQUIRED = _(u"At least one valid To: email address is required to send this message.")

UPLOAD_OFFLINE = _(u"%(accountName)s: Chandler mail is offline, \"%(subject)s\" has been queued and will be sent as soon as Mail is put back online.")

UPLOAD_START = _(u"%(accountName)s: Sending \"%(subject)s\"...")
UPLOAD_SENT = _(u"%(accountName)s: \"%(subject)s\" sent.")


# Translatable message strings for account testing
TEST_OFFLINE = _(u"Cannot perform request. Chandler mail is offline.")

#POP3 error messags
POP_UIDL_ERROR = _(u"Invalid server. The POP3 server does not support the 'UIDL' command.\nThis command is required by Chandler.")


# ChoiceFormat messages
#==========================
# L10N: This string is passed to a PyICU ChoiceFormat for formatting.
#       Contains the singular form 'message' if only
#       one message is downloaded, otherwise it uses 'messages'
#
# 1# represents the singular case
# 1< represents all cases greater than one
#
# For more information see the ICU documentation
# for the ChoiceFormat class.
#
DOWNLOAD_CHANDLER_MESSAGES = ChoiceFormat(_(u"1#%(accountName)s: %(numberTotal)s message downloaded to Chandler (New: %(numberNew)s, Updates: %(numberUpdates)s, Duplicates: %(numberDuplicates)s, Errors: %(numberErrors)s)|1<%(accountName)s: %(numberTotal)s messages downloaded to Chandler (New: %(numberNew)s, Updates: %(numberUpdates)s, Duplicates: %(numberDuplicates)s, Errors: %(numberErrors)s)"))

# L10N: This string is passed to a PyICU ChoiceFormat for formatting.
#       Contains the singular form 'message' if only
#       one message is downloaded, otherwise it uses 'messages'
#
# 1# represents the singular case
# 1< represents all cases greater than one
#
# For more information see the ICU documentation
# for the ChoiceFormat class.
#
DOWNLOAD_START_MESSAGES = ChoiceFormat(_(u"1#%(accountName)s: Downloading %(numberOfMessages)s message...|1<%(accountName)s: Downloading %(numberOfMessages)s messages..."))

POP_SEARCH_STATUS = _(u"%(accountName)s: Searching %(start)s - %(end)s of %(total)s messages...")

IMAP_SEARCH_STATUS = _(u"%(accountName)s: Searching %(start)s - %(end)s of %(total)s messages in your '%(folderDisplayName)s'...")

IMAP_INBOX_MISSING = _(u"%(accountName)s is not configured correctly.\nThe account settings contain no Inbox folder.")

IMAP_COMMIT_MESSAGES = _(u"%(accountName)s: Commiting %(start)s - %(end)s of %(total)s messages from '%(folderDisplayName)s'...")

POP_COMMIT_MESSAGES = _(u"%(accountName)s: Commiting %(start)s - %(end)s of %(total)s messages...")

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
