#   Copyright (c) 2005-2006 Open Source Applications Foundation
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


"""
Contains common utility methods shared across the
Mail Domain (SMTP, IMAP4, POP3) and message parsing
"""

#python imports
import email.Utils as Utils
import os
import logging
from time import mktime
from datetime import datetime
from PyICU import ICUtzinfo
import sys
import sgmllib
from twisted.mail import smtp
from chandlerdb.util.c import UUID

#Chandler imports
import application.Globals as Globals
from repository.util.Lob import Lob
from i18n import ChandlerMessageFactory as _

__all__ = ['log', 'trace', 'disableTwistedTLS', 'loadMailTests', 'getEmptyDate',
           'dateIsEmpty', 'alert', 'alertMailError', 'NotifyUIAsync', 'displaySSLCertDialog',
           'displayIgnoreSSLErrorDialog', 'dateTimeToRFC2822Date', 'createMessageID',
           'hasValue', 'isString', 'dataToBinary', 'binaryToData', 'stripHTML',
           'setStatusMessage', 'callMethodInUIThread']


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
    try:
        import osaf.mail.message as message
        from application import schema
        from osaf.pim import SmartCollection

        sidebar = schema.ns('osaf.app', view).sidebarCollection

        for col in sidebar:
            if unicode(dr, "utf-8") == unicode(col):
                #We already imported these mail messages
                return

        mimeDir = os.path.join(Globals.chandlerDirectory, 'parcels', 'osaf', 'mail',
                               'tests', dr)

        files = os.listdir(mimeDir)
        mCollection = SmartCollection(itsView=view)
        mCollection.displayName = unicode(dr, "utf-8")


        for f in files:
            if not f.startswith('test_'):
                continue

            filename = os.path.join(mimeDir, f)

            fp = open(filename)
            messageText = fp.read()
            fp.close()

            mailStamp = message.messageTextToKind(view, messageText)

            mCollection.add(mailStamp.itsItem)

        sidebar.add(mCollection)

    except:
        view.cancel()
        raise

def getEmptyDate():
    """
    Returns a DateTime object with today's date and the
    current Operating System timezone set to 0 ticks.
    @return: C{datetime} object
    """
    tz = ICUtzinfo.default
    return datetime.now(tz).replace(hour=0, minute=0, second=0, microsecond=0)

def dateIsEmpty(date):
    """
    Determines if a C{datetime} is empty (hh:mm:ss == 00:00:00.0).

    @param date: The date to check if it is empty
    @type date: C{datetime}

    @return: C{True} if the date is empty, False otherwise
    """
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

def alert(message, args=None):
    """
    Displays a generic alert dialog.
    """
    if args:
        message = message % args

    NotifyUIAsync(message, cl='alertUser')

def alertMailError(message, account, args=None):
    """
    Displays a mail specific alert dialog with a Edit Account Settings
    button which takes the user to the Account Dialog.
    """
    if args:
        message = message % args

    NotifyUIAsync(message, None, 'displayMailError', account)

def displaySSLCertDialog(cert, reconnectMethod):
    """
    Displays the "Do you want to add this cert" dialog.
    """
    from osaf.framework.certstore import ssl
    wxApplication = Globals.wxApplication
    if wxApplication is not None: # test framework has no wxApplication
        wxApplication.CallItemMethodAsync("MainView", 'callAnyCallable', 
                                          ssl.askTrustServerCertificate, True,
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
    if logger is not None:
        logger(message)

    wxApplication = Globals.wxApplication

    if wxApplication is not None: # test framework has no wxApplication
        wxApplication.CallItemMethodAsync("MainView", cl, message, *args, **keys)

def setStatusMessage(message, progressPercentage=-1):
    wxApplication = Globals.wxApplication

    if wxApplication is not None: # test framework has no wxApplication
        wxApplication.CallItemMethodAsync("MainView", "setStatusMessage", message, progressPercentage)

def callMethodInUIThread(method, *args):
    wxApplication = Globals.wxApplication

    if wxApplication is not None: # test framework has no wxApplication
        wxApplication.PostAsyncEvent(method, *args)


def dateTimeToRFC2822Date(dt):
    """
    Converts a C{datetime} object to a RFC2822 Date String.

    @param dt: a C{datetime} instance
    @type dt: C{datetime}

    @return: RFC2822 Date String
    """
    ticks = mktime(dt.timetuple())
    return Utils.formatdate(ticks, True)


def createMessageID():
    """
    Creates a unique message id.

    @return: String containing the unique message id
    """
    # The twisted.mail.smtp module
    # contains a cached DNS name. There
    # is a large performance increase in
    # not looking up this value each time a
    # a messageID is created.
    return "%s@%s" % (UUID().str16(), smtp.DNSNAME)


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


def dataToBinary(mailMessage, attribute, data,
                 mimeType="application/octet-stream",
                 compression='bz2', indexed=False):
    """
    Converts non-string data to a C{Lob}.
    """

    contentItem = mailMessage.itsItem
    itemAttributeName = getattr(type(mailMessage), attribute).name

    lobType = contentItem.getAttributeAspect(itemAttributeName, 'type')
    assert lobType.itsName == 'Lob', "The attribute must be of type Lob"

    return lobType.makeValue(data, mimetype=mimeType, indexed=indexed,
                             compression=compression)


def binaryToData(binary):
    """
    Converts a C{Lob} to data.
    """
    assert isinstance(binary, Lob), "Must pass a Lob instance"

    inp = binary.getInputStream()
    data = inp.read()
    inp.close()

    if binary.encoding:
        return unicode(data, binary.encoding)

    return data


class HTMLCleaner(sgmllib.SGMLParser):
    entitydefs={"nbsp": " "}

    def __init__(self):
        sgmllib.SGMLParser.__init__(self)
        self.result = []
        self.title = []

    def do_p(self, *junk):
        self.result.append(u'\n')

    def do_br(self, *junk):
        self.result.append(u'\n')

    def handle_data(self, data):
        tag = self.get_starttag_text()

        if tag != None:
            tag = tag.lower().strip()
        else:
           tag = ""

        if tag.startswith("<title"):
            self.title.append(data)

        elif tag.startswith("<script ") or \
             tag.startswith("<style "):
            pass

        else:
            self.result.append(data)

    def cleaned_text(self):
        txt = u''

        if len(self.title):
            txt += _(u"Title: ")

            for uniText in self.title:
                if isinstance(uniText, str):
                    uniText = unicode(uniText, 'utf-8', 'ignore')

                txt += uniText

            txt += u"\n\n"

        for uniText in self.result:
            if isinstance(uniText, str):
                uniText = unicode(uniText, 'utf-8', 'ignore')

            txt += uniText

        return txt

def stripHTML(text):
    cleaner = HTMLCleaner()
    cleaner.feed(text)
    return cleaner.cleaned_text()
