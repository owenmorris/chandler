#   Copyright (c) 2007 Open Source Applications Foundation
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
    'CosmoAccount',
    'CosmoConduit',
]

from application import schema
import accounts, conduits, errors, formats, eim, recordset_conduit
import zanshin
import urlparse
import logging
from i18n import ChandlerMessageFactory as _

logger = logging.getLogger(__name__)

class CosmoAccount(accounts.WebDAVAccount):

    morsecodePath = schema.One(
        schema.Text,
        doc = 'Base path on the host to use for morsecode publishing',
        initialValue = u'',
    )

    # the path attribute we inherit from WebDAVAccount represents the
    # user-facing URL, typically /cosmo/pim/collection/<uuid>


class CosmoConduit(recordset_conduit.RecordSetConduit, conduits.HTTPMixin):

    morsecodePath = schema.One(
        schema.Text,
        doc = 'Base path on the host to use for morsecode publishing when '
              'not using an account; sharePath is the user-facing path',
        initialValue = u'',
    )

    def get(self):

        location = self.getMorsecodeLocation()

        if self.syncToken:
            location += "?token=%s" % self.syncToken

        resp = self._send('GET', location)

        syncTokenHeaders = resp.headers.getHeader('X-MorseCode-SyncToken')
        if syncTokenHeaders:
            self.syncToken = syncTokenHeaders[0]
        # # @@@MOR what if this header is missing?

        return resp.body

    def put(self, text):
        location = self.getMorsecodeLocation()

        if self.syncToken:
            location += "?token=%s" % self.syncToken
            method = 'POST'
        else:
            method = 'PUT'

        resp = self._send(method, location, text)

        syncTokenHeaders = resp.headers.getHeader('X-MorseCode-SyncToken')
        if syncTokenHeaders:
            self.syncToken = syncTokenHeaders[0]
        # # @@@MOR what if this header is missing?



    def _send(self, methodName, path, body=None):

        handle = self._getServerHandle()

        extraHeaders = { }
        if hasattr(self, 'ticket'):
            extraHeaders['Ticket'] = self.ticket

        request = zanshin.http.Request(methodName, path, extraHeaders, body)

        try:
            return handle.blockUntil(handle.addRequest, request)

            # @@@MOR Should I check the response.status here or in the caller?

        except zanshin.webdav.ConnectionError, err:
            raise errors.CouldNotConnect(_(u"Unable to connect to server. Received the following error: %(error)s") % {'error': err})

        except M2Crypto.BIO.BIOError, err:
            raise errors.CouldNotConnect(_(u"Unable to connect to server. Received the following error: %(error)s") % {'error': err})


    def getMorsecodeLocation(self, privilege=None):
        """
        Return the morsecode url of the share
        """

        (host, port, path, username, password, useSSL) = \
            self._getMorsecodeSettings()
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
            url = urlparse.urljoin(url, path)
        else:
            url = urlparse.urljoin(url, path + "/")
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


    def _getMorsecodeSettings(self):
        if self.account is None:
            return (self.host, self.port, self.morsecodePath.strip("/"),
                    self.username, self.password, self.useSSL)
        else:
            return (self.account.host, self.account.port,
                    self.account.morsecodePath.strip("/"),
                    self.account.username, self.account.password,
                    self.account.useSSL)


