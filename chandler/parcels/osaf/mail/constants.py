__revision__  = "$Revision$"
__date__      = "$Date$"
__copyright__ = "Copyright (c) 2005 Open Source Applications Foundation"
__license__   = "http://osafoundation.org/Chandler_0.1_license_terms.htm"

""" Contains constants shared across the Mail Domain (SMTP, IMAP4, POP3) """

#python / mx imports
import version



#XXX: This will go away with internationalization
DEFAULT_CHARSET = "ascii"

CHANDLER_USERAGENT = "Chandler (%s %s)" % (version.release, version.build)
CHANDLER_HEADER_PREFIX = "X-Chandler-"
ATTACHMENT_BODY_WARNING = "\tThe body of this message consists of Multiple Mime Parts.\n\t%s does not support MIME Parts" % CHANDLER_USERAGENT

"""MIME TYPE SPECS"""

MIME_TEXT_PLAIN = "text/plain"
MIME_APPLEFILE = "application/applefile"

MIME_TEXT = ["plain", "html", "enriched", "sgml", "richtext", "rfc-headers"]
MIME_BINARY = ["image", "application", "audio", "video"]
MIME_SECURITY = ["encrypted", "signed"]
MIME_CONTAINER = ["alternative", "parallel", "related", "report", "partial", "digest"]

DATE_IS_EMPTY = -57600
TIMEOUT = 60

SHARING_HEADER  = "Sharing-URL"
SHARING_DIVIDER = ";"
SMTP_SUCCESS = 250


