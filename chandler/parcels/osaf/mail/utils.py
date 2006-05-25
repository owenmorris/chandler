"""
Contains common utility methods shared across the
Mail Domain (SMTP, IMAP4, POP3) and message parsing

@copyright: Copyright (c) 2005-2006 Open Source Applications Foundation
@license: U{http://osafoundation.org/Chandler_0.1_license_terms.htm}
"""

#python imports
import email.Utils as Utils
import os
import logging
from time import mktime
from datetime import datetime
import sys

#Chandler imports
import application.Globals as Globals
from repository.util.Lob import Lob

#Chandler Mail Service imports
import constants as constants

__all__ = ['log', 'trace', 'disableTwistedTLS', 'loadMailTests', 'getEmptyDate',
           'dateIsEmpty', 'alert', 'alertMailError', 'NotifyUIAsync', 'displaySSLCertDialog',
           'displayIgnoreSSLErrorDialog', 'dateTimeToRFC2882Date', 'createMessageID',
           'hasValue', 'isString', 'dataToBinary',
           'binaryToData']


log = logging.getLogger("MailService")

def trace(printString):

    if printString is not None:
        if isinstance(printString, Exception):
            return log.exception(printString)

        frame = sys._getframe(1)
        """
        Get the package and class name from the frame stack
        """
        caller = frame.f_locals.get('self')

        if caller is not None:
            """
            Strip off the package path and trailing '> on new style classes
            """
            caller = str(caller.__class__).split(".")[-1].rstrip("'>")
            log.debug("[%s] %s " % (caller, printString))
        else:
            log.debug("%s " % printString)

class Counter:
    def __init__(self, val=0):
        self.counter = val

    def nextValue(self):
        self.counter += 1
        return self.counter


def loadMailTests(view, dr):
    import osaf.mail.message as message

    mimeDir = os.path.join(Globals.chandlerDirectory, 'parcels', 'osaf', 'mail',
                           'tests', dr)

    files = os.listdir(mimeDir)

    for f in files:
        if not f.startswith('test_'):
            continue

        if message.verbose():
            logging.warn("Opening File: %s" % f)

        filename = os.path.join(mimeDir, f)

        fp = open(filename)
        messageText = fp.read()
        fp.close()

        message.messageTextToKind(view, messageText)

    view.commit()

def getEmptyDate():
    """
    Returns a DateTime object set to 0 ticks.
    @return: C{datetime} object
    """

    return datetime.today().replace(hour=0, minute=0, second=0, microsecond=0)

def dateIsEmpty(date):
    """
    Determines if a C{datetime} is empty (hh:mm:ss == 00:00:00.0).

    @param date: The date to check if it is empty
    @type date: C{datetime}

    @return: C{True} if the date is empty, False otherwise
    """
    #XXX: Need to protect this better but having trouble with
    #     the datetime API
    if date is None or (date.hour == 0 and date.minute == 0 and
                        date.second == 0 and date.microsecond == 0):
        return True

    return False


def disableTwistedTLS(items, TLSKEY='STARTTLS'):
    """
    Disables SSL support for debugging so
    a tcpflow trace can be done on the Client / Server
    command exchange.

    @param TLSKEY: String key to remove from items list
    @type TLSKEY: C{String}
    """

    if items != None and TLSKEY != None:
        try:
            del items[TLSKEY]
        except KeyError:
            pass

    return items

def alert(message, args):
    """
    Displays a generic alert dialog.
    """
    NotifyUIAsync(message % args, cl='alertUser')

def alertMailError(message, account, args):
    """
    Displays a mail specific alert dialog with a Edit Account Settings
    button which takes the user to the Account Dialog.
    """
    NotifyUIAsync(message % args, None, 'displayMailError', account)

def displaySSLCertDialog(cert, reconnectMethod):
    """
    Displays the "Do you want to add this cert" dialog.
    """
    from osaf.framework.certstore import ssl
    wxApplication = Globals.wxApplication
    if wxApplication is not None: # test framework has no wxApplication
        wxApplication.CallItemMethodAsync("MainView", 'callAnyCallable', 
                                          ssl.askTrustSiteCertificate, True,
                                          cert, reconnectMethod)

def displayIgnoreSSLErrorDialog(cert, err, reconnectMethod):
    """
    Displays the invalid cert dialog.
    """
    from osaf.framework.certstore import ssl
    wxApplication = Globals.wxApplication
    if wxApplication is not None: # test framework has no wxApplication
        wxApplication.CallItemMethodAsync("MainView", 'callAnyCallable',
                                          ssl.askIgnoreSSLError, False, cert,
                                          err, reconnectMethod)

def NotifyUIAsync(message, logger=None, cl='setStatusMessage', *args, **keys):
    """
    Temp method for posting a event to the CPIA layer.
    This method will be refactored when notifcations come in to play.
    """

    if logger is not None:
        logger(message)

    wxApplication = Globals.wxApplication

    if wxApplication is not None: # test framework has no wxApplication
        wxApplication.CallItemMethodAsync("MainView", cl, message, *args, **keys)


def dateTimeToRFC2882Date(dt):
    """
    Converts a C{datetime} object to a RFC2882 Date String.

    @param dt: a C{datetime} instance
    @type dt: C{datetime}

    @return: RFC2882 Date String
    """
    ticks = mktime(dt.timetuple())
    return Utils.formatdate(ticks, True)


def createMessageID():
    """
    Creates a unique message id.

    @return: String containing the unique message id
    """
    return Utils.make_msgid()


def hasValue(value):
    """
    This method determines if a String has one or more non-whitespace
    characters. This is useful in checking that a Subject or To address
    field was filled in with a useable value.

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


def dataToBinary(contentItem, attribute, data,
                 mimeType="application/octet-stream",
                 compression='bz2', indexed=False):
    """
    Converts non-string data to a C{TLob}.
    """
    lobType = contentItem.getAttributeAspect(attribute, 'type')
    assert lobType.itsName == 'Lob', "The attribute must be of type Lob"

    return lobType.makeValue(data, mimetype=mimeType, indexed=indexed,
                             compression=compression)


def binaryToData(binary):
    """
    Converts a C{Lob} to data.
    """
    assert isinstance(binary, Lob), "Must pass a Lob instance"
    assert binary.encoding is None, "Encoding must be None for inputstreamr API"

    inp = binary.getInputStream()
    data = inp.read()
    inp.close()

    return data
