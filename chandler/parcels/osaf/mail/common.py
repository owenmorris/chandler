__revision__  = "$Revision$"
__date__      = "$Date$"
__copyright__ = "Copyright (c) 2004 Open Source Applications Foundation"
__license__   = "http://osafoundation.org/Chandler_0.1_license_terms.htm"

""" Contains common functionality shared across the Mail Domain (SMTP, IMAP4, POP3) """


import email as email
import email.Message as Message
import email.Utils as Utils
import mx.DateTime as DateTime

CHANDLER_USERAGENT = "Chandler/.4B Release"
CHANDLER_HEADER_PREFIX = "X-Chandler-"
ATTACHMENT_BODY_WARNING = "\tThe body of this message consists of Multiple Mime Parts.\n\tFor .4B Chandler does not support MIME Parts"

"""MIME TYPE SPECS"""

MIME_TEXT_PLAIN = "text/plain"

MIME_TEXT = ["plain", "html", "enriched", "sgml", "richtext", "rfc-headers"]
MIME_BINARY = ["image", "application", "audio", "video"]
MIME_SECURITY = ["encrypted", "signed"]
MIME_CONTAINER = ["alternative", "parallel", "related", "report", "partial", "digest"]

DATE_IS_EMPTY = -57600

class MailException(Exception):
    """Base class for all Chandler mail related exceptions"""
    pass

def getChandlerTransportMessage():
    """Returns the skeleton of a mail message populated with the subject
       and body verbage Chandler uses when the message in not intended to
       be view by users i.e. a sharing invitation."""

    message = \
"""Subject: ***FOR CHANDLER INTERNAL USE - DO NOT DELETE ***

This message is used for Chandler to Chandler communication and is
not intended to be viewed by the user. Please do not delete this message
as Chandler will manage this email automatically for you.
"""

    return email.message_from_string(message)


def getEmptyDate():
    """Returns a DateTime object set to 0 ticks.
       @return: C{mx.DateTime} object"""

    return DateTime.DateFromTicks(0)

def dateIsEmpty(date):
    """Determines if a C{mx.DateTime} is empty (set to 0 ticks).

       @param date: The date to check if it is empty
       @type date: C{mx.DateTime}

       @return bool: True if the date is empty, False otherwise
    """
    #XXX: Need to protect this better but having trouble with
    #     the mx.DateTime API
    if date is None or date.ticks() == DATE_IS_EMPTY:
        return True

    return False

def disableTwistedTLS(items):
    """Disables SSL support for debugging so
       a tcpflow trace can be done on the Client / Server
       command exchange
    """

    if items != None:
        try:
            del items["STARTTLS"]

        except KeyError:
            pass

    return items


