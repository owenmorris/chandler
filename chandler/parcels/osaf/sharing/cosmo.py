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
import shares, accounts, conduits, errors, formats, eim, recordset_conduit
import translator, eimml
import zanshin, M2Crypto
import urlparse
import logging
import time
from i18n import ChandlerMessageFactory as _

logger = logging.getLogger(__name__)

class CosmoAccount(accounts.WebDAVAccount):

    # The path attribute we inherit from WebDAVAccount represents the
    # base path of the Cosmo installation, typically "/cosmo".  The
    # following attributes store paths relative to WebDAVAccount.path

    pimPath = schema.One(
        schema.Text,
        doc = 'Base path on the host to use for the user-facing urls',
        initialValue = u'pim/collection',
    )

    morsecodePath = schema.One(
        schema.Text,
        doc = 'Base path on the host to use for morsecode publishing',
        initialValue = u'mc/collection',
    )

    davPath = schema.One(
        schema.Text,
        doc = 'Base path on the host to use for DAV publishing',
        initialValue = u'dav/collection',
    )

    accountProtocol = schema.One(
        initialValue = 'Morsecode',
    )

    accountType = schema.One(
        initialValue = 'SHARING_MORSECODE',
    )

    def publish(self, collection, updateCallback=None, filters=None):
        rv = self.itsView

        share = shares.Share(itsView=rv, contents=collection)
        shareName = collection.itsUUID.str16()
        conduit = CosmoConduit(itsParent=share, shareName=shareName,
            account=self,
            translator=translator.PIMTranslator,
            serializer=eimml.EIMMLSerializer)

        if filters:
            conduit.filters = filters

        share.conduit = conduit

        share.put(updateCallback=updateCallback)

        return [share]


class CosmoConduit(recordset_conduit.DiffRecordSetConduit, conduits.HTTPMixin):

    morsecodePath = schema.One(
        schema.Text,
        doc = 'Base path on the host to use for morsecode publishing when '
              'not using an account; sharePath is the user-facing path',
        initialValue = u'',
    )

    def sync(self, modeOverride=None, updateCallback=None, forceUpdate=None,
        debug=False):

        startTime = time.time()
        self.networkTime = 0.0

        stats = super(CosmoConduit, self).sync(modeOverride=modeOverride,
            updateCallback=updateCallback, forceUpdate=forceUpdate,
            debug=debug)

        endTime = time.time()
        duration = endTime - startTime
        logger.info("Sync took %6.2f seconds (network = %6.2f)", duration,
            self.networkTime)

        return stats

    def get(self):

        location = self.getMorsecodeLocation()

        resp = self._send('GET', location)
        if resp.status != 200:
            # TODO: Fix error message
            raise errors.SharingError("HTTP error %d" % resp.status,
                debugMessage="Sent [%s], Received [%s]" % (text, resp.body))

        syncTokenHeaders = resp.headers.getHeader('X-MorseCode-SyncToken')
        if syncTokenHeaders:
            self.syncToken = syncTokenHeaders[0]
        # # @@@MOR what if this header is missing?

        return resp.body

    def put(self, text):

        location = self.getMorsecodeLocation()

        if self.syncToken:
            method = 'POST'
        else:
            method = 'PUT'

        resp = self._send(method, location, text)

        if resp.status in (205, 423):
            # The collection has either been updated by someone else since
            # we last did a GET (205) or the collection is in the process of
            # being updated right now and is locked (423).  In each case, our
            # reaction is the same -- abort the sync.
            # TODO: We should try to sync again soon
            raise errors.TokenMismatch(_(u"Collection updated by someone else"))

        elif resp.status not in (201, 204):
            raise errors.SharingError("HTTP error %d" % resp.status,
                debugMessage="Sent [%s], Received [%s]" % (text, resp.body))

        syncTokenHeaders = resp.headers.getHeader('X-MorseCode-SyncToken')
        if syncTokenHeaders:
            self.syncToken = syncTokenHeaders[0]
        # # @@@MOR what if this header is missing?

    def destroy(self):
        location = self.getMorsecodeLocation()
        resp = self._send('DELETE', location)
        if resp.status != 204:
            raise errors.SharingError("HTTP error %d" % resp.status,
                debugMessage="Sent [%s], Received [%s]" % (text, resp.body))

    def create(self):
        pass

    def _send(self, methodName, path, body=None):
        # Caller must check resp.status themselves

        handle = self._getServerHandle()

        extraHeaders = { }

        ticket = getattr(self, 'ticket', None)
        if ticket:
            extraHeaders['Ticket'] = ticket

        syncToken = getattr(self, 'syncToken', None)
        if syncToken:
            extraHeaders['X-MorseCode-SyncToken'] = syncToken

        extraHeaders['Content-Type'] = 'application/eim+xml'

        request = zanshin.http.Request(methodName, path, extraHeaders, body)

        try:
            start = time.time()
            response = handle.blockUntil(handle.addRequest, request)
            end = time.time()
            self.networkTime += (end - start)
            return response

        except zanshin.webdav.ConnectionError, err:
            raise errors.CouldNotConnect(_(u"Unable to connect to server. Received the following error: %(error)s") % {'error': err})

        except M2Crypto.BIO.BIOError, err:
            raise errors.CouldNotConnect(_(u"Unable to connect to server. Received the following error: %(error)s") % {'error': err})


    def getLocation(self, privilege=None):
        """
        Return the user-facing url of the share
        """

        (host, port, path, username, password, useSSL) = \
            self._getSettings()
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

    def _getSettings(self):
        if self.account is None:
            return (self.host, self.port, self.sharePath.strip("/"),
                    self.username, self.password, self.useSSL)
        else:
            path = self.account.path.strip("/") + "/" + self.account.pimPath
            return (self.account.host, self.account.port,
                    path.strip("/"),
                    self.account.username, self.account.password,
                    self.account.useSSL)



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
            path = self.account.path.strip("/") + "/" + self.account.morsecodePath
            return (self.account.host, self.account.port,
                    path.strip("/"),
                    self.account.username, self.account.password,
                    self.account.useSSL)


    def getFilter(self):
        # This is where we can filter out things we don't want to send to
        # Cosmo
        filter = super(CosmoConduit, self).getFilter()
        filter += eim.lookupSchemaURI('cid:non-standard-ical-filter@osaf.us')
        return filter
