#   Copyright (c) 2003-2007 Open Source Applications Foundation
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

import traceback, sys
import logging
logger = logging.getLogger(__name__)

from osaf import ChandlerException


def annotate(exception, brief, details=""):
    if not hasattr(exception, 'annotations'):
        exception.annotations = [ (str(exception), "") ]

    exception.annotations.append( (brief, details) )


def formatException(exception):
    summary = []
    extended = []

    # Turn the stack and exception into a string
    stack = "".join(traceback.format_tb(sys.exc_info()[2]))
    stack += "%s %s" % sys.exc_info()[0:2]

    if hasattr(exception, 'annotations'):
        # This exception has been annotated along the way
        for brief, details in exception.annotations[::-1]:
            summary.append(brief)
            extended.append(details)
    else:
        summary.append(str(exception.message or type(exception)))
        details = getattr(exception, 'debugMessage', None)
        if details:
            extended.append(str(details))

    summary = " | ".join(summary)

    extended.append(stack)

    extended = "\n--\n".join(extended)

    return summary, extended



class SharingError(ChandlerException):
    def __init__(self, message, details="", exception=None, debugMessage=None):
        super(SharingError, self).__init__(message, exception=exception,
            debugMessage=debugMessage)
        self.annotations = []
        annotate(self, message, details=details)

class AlreadyExists(SharingError):
    """
    Exception raised if a share already exists.
    """

class NotFound(SharingError):
    """
    Exception raised if a share/resource wasn't found.
    """

class NotAllowed(SharingError):
    """
    Exception raised if we don't have access.
    """

class Misconfigured(SharingError):
    """
    Exception raised if a share isn't properly configured.
    """

class CouldNotConnect(SharingError):
    """
    Exception raised if a conduit can't connect to an external entity
    due to DNS/network problems.
    """

class IllegalOperation(SharingError):
    """
    Exception raised if the entity a conduit is communicating with is
    denying an operation for some reason not covered by other exceptions.
    """

class MalformedData(SharingError):
    """
    Exception raised when importProcess fails because of malformed data
    """

class TransformationFailed(SharingError):
    """
    Exception raised if export process failed
    """

class AlreadySubscribed(SharingError):
    """
    Exception raised if subscribing to an already-subscribed url
    """

class VersionMismatch(SharingError):
    """
    Exception raised if syncing with a CloudXML share of an old version
    """

class TokenMismatch(SharingError):
    """
    Exception raised when we perform a Cosmo operation and our sync token
    is out of date
    """

class MalformedToken(SharingError):
    """
    Exception raised when we pass a token which Cosmo doesn't understand
    """

class ConflictsPending(SharingError):
    """
    Exception raised if attempting to send a p2p change with conflicts pending
    """

class OutOfSequence(SharingError):
    """
    Exception raised if an old itemcentric update arrives after a more recent
    One
    """

class OfflineError(SharingError):
    """
    Exception raised if attempting to publish or subscribe while in offline mode
    """

class URLParseError(SharingError):
    """
    Exception raised if a subscribe URL cannot be parsed
    """

class WebPageParseError(SharingError):
    """
    Exception raised if a web page cannot be parsed for embedded collection info
    """

class DuplicateIcalUids(SharingError):
    """
    Exception raised if two items in the same collection have the same icaluid
    """
