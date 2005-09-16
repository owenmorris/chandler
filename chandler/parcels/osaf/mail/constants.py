__revision__  = "$Revision$"
__date__      = "$Date$"
__copyright__ = "Copyright (c) 2005 Open Source Applications Foundation"
__license__   = "http://osafoundation.org/Chandler_0.1_license_terms.htm"

""" Contains constants shared across the Mail Domain (SMTP, IMAP4, POP3) """

#XXX: Look at moving much of the data to items

#python imports
import version

from i18n import OSAFMessageFactory as _

DEFAULT_CHARSET = "utf-8"
LF    = u"\n"
CR    = u"\r"
EMPTY = u""

CHANDLER_USERAGENT = "Chandler (%s %s)" % (version.release, version.build)
CHANDLER_HEADER_PREFIX = "X-Chandler-"

INVALID_EMAIL_ADDRESS = _(u"Email Address %(emailAddress)s is not valid")

UNKNOWN_ERROR = _(u"An unknown error has occurred")

"""Translatable message strings for downloads (POP, IMAP)"""
DOWNLOAD_ERROR = _(u"An error occurred while downloading:\n%(error)s")
DOWNLOAD_NO_MESSAGES = _(u"No new messages found")
DOWNLOAD_MESSAGES = _(u"%(numberOfMessages)s messages downloaded to Chandler")
DOWNLOAD_CHECK_MESSAGES = _(u"Checking for new mail messages")
DOWNLOAD_REQUIRES_TLS = _(u"The Server only allows secure login. Please enable TLS or SSL.")

"""Translatable message strings for uploads(SMTP)"""
UPLOAD_BAD_REPLY_ADDRESS = _(u"The Reply-To Address %(emailAddress)s is not valid")
UPLOAD_FROM_REQUIRED = _(u"A From Address is required to send a Mail Message")
UPLOAD_TO_REQUIRED = _(u"A To Address is required to send an SMTP Mail Message")


"""Translatable message strings for account testing"""
TEST_ERROR = _(u"%(accountName)s Results\n\nPlease correct the following configuration error:\n\n%(error)s")
TEST_SUCCESS = _(u"%(accountName)s Results\n\nTest was successful.")

SHARING_HEADER  = "Sharing-URL"
SHARING_DIVIDER = ";"
SMTP_SUCCESS = 250

"""Number of seconds to wait to timeout connection for account testing"""
TESTING_TIMEOUT = 10

"""If set to True dumps MailMessage structure
   during parsing to the chandler.log.
   This will only work in debugging mode
   i.e. __debug__ == True
"""
VERBOSE = False
