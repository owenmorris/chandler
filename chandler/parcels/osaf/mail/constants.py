__revision__  = "$Revision$"
__date__      = "$Date$"
__copyright__ = "Copyright (c) 2005 Open Source Applications Foundation"
__license__   = "http://osafoundation.org/Chandler_0.1_license_terms.htm"

""" Contains constants shared across the Mail Domain (SMTP, IMAP4, POP3) """

#python / mx imports
import version

#XXX: This will go away with internationalization
DEFAULT_CHARSET = "utf-8"

CHANDLER_USERAGENT = "Chandler (%s %s)" % (version.release, version.build)
CHANDLER_HEADER_PREFIX = "X-Chandler-"

DATE_IS_EMPTY = -57600
TIMEOUT = 60

SHARING_HEADER  = "Sharing-URL"
SHARING_DIVIDER = ";"
SMTP_SUCCESS = 250

VERBOSE = False


