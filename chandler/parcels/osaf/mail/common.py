__revision__  = "$Revision$"
__date__      = "$Date$"
__copyright__ = "Copyright (c) 2004 Open Source Applications Foundation"
__license__   = "http://osafoundation.org/Chandler_0.1_license_terms.htm"

""" Contains common functionality shared across the Mail Domain (SMTP, IMAP4, POP3) """


import email as email
import email.Message as Message
import email.Utils as Utils

CHANDLER_USERAGENT = "Open Source Applications Foundation Chandler .4B Release"
CHANDLER_HEADER_PREFIX = "X-Chandler-"
ATTACHMENT_BODY_WARNING = "\tThe body of this message consists of Multiple Mime Parts.\n\tFor .4B Chandler does not support MIME Parts"

"""MIME TYPE SPECS"""

MIME_TEXT_PLAIN = "text/plain"

MIME_TEXT = ["plain", "html", "enriched", "sgml", "richtext", "rfc-headers"]
MIME_BINARY = ["image", "application", "audio", "video"]
MIME_SECURITY = ["encrypted", "signed"]
MIME_CONTAINER = ["alternative", "parallel", "related", "report", "partial", "digest"]

class MailException(Exception):
    pass

def getChandlerTransportMessage():
    message = """Subject: ***FOR CHANDLER INTERNAL USE - DO NOT DELETE ***

    This message is used for Chandler to Chandler communication and is
    not intended to be viewed by the user. Please do not delete this message
    as Chandler will manage this email automatically for you.

    """

    return email.message_from_string(message)
