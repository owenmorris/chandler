#   Copyright (c) 2003-2006 Open Source Applications Foundation
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

import logging
logger = logging.getLogger(__name__)

from osaf import ChandlerException
from i18n import ChandlerMessageFactory as _


class SharingError(ChandlerException):
    pass


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

