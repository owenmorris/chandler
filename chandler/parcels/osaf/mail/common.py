__revision__  = "$Revision$"
__date__      = "$Date$"
__copyright__ = "Copyright (c) 2004 Open Source Applications Foundation"
__license__   = "http://osafoundation.org/Chandler_0.1_license_terms.htm"

""" Contains common functionality shared across the Mail Domain (SMTP, IMAP4, POP3) """

#python / mx imports
import email as email
import email.Message as Message
import email.Utils as Utils
import mx.DateTime as DateTime
import version

#Chandler imports
#XXX: This is a bad import in the GUI layer. Will remove when notifications figured out
import application.Globals as Globals


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

class SharingConstants:
    SHARING_HEADER  = "Sharing-URL"
    SHARING_DIVIDER = ";"

class SMTPConstants:
    SUCCESS = 250

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


def NotifyUIAsync(message, logger=None, callable='setStatusMessage', **keys):
    """Temp method for posting a event to the CPIA layer. This
       method will be refactored soon"""

    if logger is not None:
        logger(message)

    if Globals.wxApplication is not None: # test framework has no wxApplication
        Globals.wxApplication.CallItemMethodAsync(Globals.views[0], callable,
                                                   message, **keys)
