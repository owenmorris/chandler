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


__all__ = [
    'Conduit',
    'BaseConduit',
    'HTTPMixin',
]

import shares, errors, utility
from callbacks import *
from application import schema
from osaf import pim
from osaf.framework.twisted import waitForDeferred
from osaf.framework.password import passwordAttribute
from repository.item.Item import Item
from chandlerdb.util.c import UUID
import zanshin, M2Crypto.BIO, twisted.web.http
import logging
import WebDAV
import urlparse
import datetime
from i18n import ChandlerMessageFactory as _


logger = logging.getLogger(__name__)





class Conduit(pim.ContentItem):
    share = schema.One(shares.Share, inverse=shares.Share.conduit)

    def sync(self, modeOverride=None, activity=None, forceUpdate=None,
        debug=False):
        raise NotImplementedError


class BaseConduit(Conduit):

    sharePath = schema.One(
        schema.Text, initialValue=u"",
        doc = "The parent 'directory' of the share",
    )

    shareName = schema.One(
        schema.Text, initialValue=u"",
        doc = "The 'directory' name of the share, relative to 'sharePath'",
    )

    schema.initialValues(
        shareName = lambda self: unicode(UUID()),
    )

    # TODO: see if this is used anymore:

    def isAttributeModifiable(self, item, attribute):
        share = self.share

        if utility.isSharedByMe(share) or share.mode in ('put', 'both'):
            return True

        # In old style shares, an attribute isn't modifiable if it's one
        # of the attributes shared for this item in this share
        for attr in item.getBasedAttributes(attribute):
            if attr in share.getSharedAttributes(item.itsKind):
                return False

        return True








class HTTPMixin(BaseConduit):

    account = schema.One(initialValue=None)
    host = schema.One(schema.Text, initialValue=u"")
    port = schema.One(schema.Integer, initialValue=80)
    username = schema.One(schema.Text, initialValue=u"")
    password = passwordAttribute
    useSSL = schema.One(schema.Boolean, initialValue=False)

    # The ticket this conduit will use (we're a sharee and we're using this)
    ticket = schema.One(schema.Text, initialValue="")

    # The tickets we generated if we're a sharer
    ticketReadOnly = schema.One(schema.Text, initialValue="")
    ticketReadWrite = schema.One(schema.Text, initialValue="")

    def __setup__(self):
        self.onItemLoad() # Get a chance to clear out old connection

    def onItemLoad(self, view=None):
        self.serverHandle = None

    def _getSettings(self, withPassword=True):
        password = None
        if self.account is None:
            if withPassword:
                password = getattr(self, "password", None)
                if password:
                    password = waitForDeferred(password.decryptPassword())
            return (self.host, self.port,
                    self.sharePath.strip("/"),
                    self.username,
                    password,
                    self.useSSL)
        else:
            if withPassword:
                password = getattr(self.account, "password", None)
                if password:
                    password = waitForDeferred(password.decryptPassword())
            return (self.account.host, self.account.port,
                    self.account.path.strip("/"),
                    self.account.username,
                    password,
                    self.account.useSSL)

    def _getServerHandle(self):
        # @@@ [grant] Collections and the trailing / issue.
        if self.serverHandle == None:
            # logger.debug("...creating new webdav ServerHandle")
            (host, port, sharePath, username, password, useSSL) = \
            self._getSettings()

            self.serverHandle = WebDAV.ChandlerServerHandle(host, port=port,
                username=username, password=password, useSSL=useSSL,
                repositoryView=self.itsView)

        return self.serverHandle

    def _releaseServerHandle(self):
        self.serverHandle = None


    def getLocation(self, privilege=None):
        """
        Return the url of the share
        """

        (host, port, sharePath, username, password, useSSL) = \
            self._getSettings(withPassword=False)
        if useSSL:
            scheme = u"https"
            defaultPort = 443
        else:
            scheme = u"http"
            defaultPort = 80

        if port == defaultPort:
            url = u"%s://%s" % (scheme, host)
        else:
            url = u"%s://%s:%d" % (scheme, host, port)
        if self.shareName == '':
            url = urlparse.urljoin(url, sharePath)
        else:
            url = urlparse.urljoin(url, sharePath + "/")
            url = urlparse.urljoin(url, self.shareName)

        if privilege == 'readonly':
            if self.ticketReadOnly:
                url = url + u"?ticket=%s" % self.ticketReadOnly
        elif privilege == 'readwrite':
            if self.ticketReadWrite:
                url = url + u"?ticket=%s" % self.ticketReadWrite
        elif privilege == 'subscribed':
            if self.ticket:
                url = url + u"?ticket=%s" % self.ticket

        return url
