__revision__  = "$Revision$"
__date__      = "$Date$"
__copyright__ = "Copyright (c) 2005 Open Source Applications Foundation"
__license__   = "http://osafoundation.org/Chandler_0.1_license_terms.htm"

""" Contains common utility methods shared across the Mail Domain (SMTP, IMAP4, POP3) and message parsing"""

#python / mx imports
import email as email
import email.Message as Message
import email.Utils as Utils
import os
import mx.DateTime as DateTime
import logging

#Chandler imports
import application.Globals as Globals
from repository.util.Lob import Lob

#Chandler Mail Service imports
import constants as constants

class Counter:
    def __init__(self, val=0):
        self.counter = val

    def nextValue(self):
        self.counter += 1
        return self.counter


def loadMailTests(view, dir):
    import osaf.mail.message as message
    import osaf.contentmodel.mail.Mail as Mail

    mimeDir = os.path.join(Globals.chandlerDirectory, 'parcels', 'osaf', 'mail',
                           'tests', dir)

    files = os.listdir(mimeDir)

    for file in files:
        if not file.startswith('test_'):
            continue

        if message.verbose():
            logging.warn("Opening File: %s" % file)

        filename = os.path.join(mimeDir, file)

        fp = open(filename)
        messageText = fp.read()
        fp.close()

        mailMessage = message.messageTextToKind(view, messageText)

    view.commit()


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

    wxApplication = Globals.wxApplication
    if wxApplication is not None: # test framework has no wxApplication
        wxApplication.CallItemMethodAsync(Globals.views[0], callable,
                                          message, **keys)


def dateTimeToRFC2882Date(dateTime):
    """Converts a C{mx.DateTime} object to a
       RFC2882 Date String

       @param dateTime: a C{mx.DateTime} instance
       @type dateTime: C{mx.DateTime}

       @return: RFC2882 Date String
    """
    return Utils.formatdate(dateTime.ticks(), True)


def createMessageID():
    """Creates a unique message id
       @return: String containing the unique message id"""
    return Utils.make_msgid()


def hasValue(value):
    """
    This method determines if a String has one or more non-whitespace characters.
    This is useful in checking that a Subject or To address field was filled in with
    a useable value

    @param value: The String value to check against. The value can be None
    @type value: C{String}
    @return: C{Boolean}
    """
    if isString(value) and len(value.strip()) > 0:
        return True

    return False

def isString(var):
    if isinstance(var, (str, unicode)):
        return True

    return False

def strToText(contentItem, attribute, unicodeString, indexText=False, \
              encoding=constants.DEFAULT_CHARSET):
    #XXX: Should rename this method to be more clear
    """Converts a C{unicode} string  to {Lob}.
    """
    assert isinstance(unicodeString, unicode), "Only Unicode string may be passed to this method"

    return contentItem.getAttributeAspect(attribute, \
                                          'type').makeValue(unicodeString, \
                                          indexed=indexText, encoding=encoding)


def textToStr(text):
    #XXX: Should rename this method to be more clear
    """Converts a text C{Lob} to a C{unicode} String"""
    assert isinstance(text, Lob), "Must pass a Lob instance"
    assert text.encoding, "Encoding must not be None for reader API"

    reader = text.getReader()
    uStr = reader.read()
    reader.close()

    return uStr

def dataToBinary(contentItem, attribute, data, compression=None, indexText=False):
    """Converts non-string data to a C{TLob}
    """
    binary =  contentItem.getAttributeAspect(attribute, \
                                          'type').makeValue(None, \
                                          indexed=indexText, encoding=None)

    if compression:
        binaryStream = binary.getOutputStream(compression=compression)

    else:
        binaryStream = binary.getOutputStream()

    binaryStream.write(data)
    binaryStream.close()

    return binary


def binaryToData(binary):
    """Converts a C{Lob} to data"""
    assert isinstance(binary, Lob), "Must pass a Lob instance"
    assert binary.encoding is None, "Encoding must be None for inputstreamr API"

    input = binary.getInputStream()
    data = input.read()
    input.close()

    return data
