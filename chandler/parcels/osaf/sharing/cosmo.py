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
    'HubAccount',
    'CosmoConduit',
]

from application import schema
import shares, accounts, conduits, errors, eim, recordset_conduit, viewpool
from shares import Share
from osaf.activity import Activity, ActivityAborted
import translator, eimml, WebDAV, utility
import zanshin, M2Crypto
import urlparse, urllib
import logging
import time
from i18n import ChandlerMessageFactory as _
from osaf.framework.twisted import waitForDeferred
from xml.etree.cElementTree import fromstring
import twisted.internet.error
import threading
from osaf.mail.utils import callMethodInUIThread

logger = logging.getLogger(__name__)


mcURI = "http://osafoundation.org/mc/"





class CosmoAccount(accounts.SharingAccount):

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

    # modify this only in sharing view to avoid merge conflicts
    unsubscribed = schema.Many(schema.Text, initialValue=set(),
        doc = 'UUIDs of unsubscribed collections the user has not acted upon')

    # modify this only in main view to avoid merge conflicts
    ignored = schema.Many(schema.Text, initialValue=set(),
        doc = 'UUIDs of unsubscribed collections the user chose to ignore')

    # modify this only in main view to avoid merge conflicts
    requested = schema.Many(schema.Text, initialValue=set(),
        doc = 'UUIDs of unsubscribed collections the user wants to restore')

    def publish(self, collection, displayName=None, activity=None, filters=None,
        overwrite=False, options=None):

        rv = self.itsView

        share = shares.Share(itsView=rv, contents=collection)
        shareName = collection.itsUUID.str16()
        conduit = CosmoConduit(itsParent=share, shareName=shareName,
            account=self,
            translator=translator.SharingTranslator,
            serializer=eimml.EIMMLSerializer)

        if filters:
            conduit.filters = filters

        share.conduit = conduit


        if overwrite:
            if activity:
                activity.update(totalWork=None,
                    msg=_(u"Removing old collection from server..."))
            share.destroy()

        share.put(activity=activity)

        return share


    def getPublishedShares(self, callback=None, blocking=False):
        if blocking:
            return self._getPublishedShares(None)

        # don't block the current thread
        t = threading.Thread(target=self._getPublishedShares,
            args=(callback,))
        t.start()

    def _getPublishedShares(self, callback):
        path = self.path.strip("/")
        if path:
            path = "/%s" % path
        path = urllib.quote("%s/mc/user/%s" % (path, self.username))
        handle = WebDAV.ChandlerServerHandle(self.host, self.port,
            username=self.username,
            password=waitForDeferred(self.password.decryptPassword()),
            useSSL=self.useSSL, repositoryView=self.itsView)

        extraHeaders = {}
        body = None
        request = zanshin.http.Request('GET', path, extraHeaders, body)

        try:
            resp = handle.blockUntil(handle.addRequest, request)
        except zanshin.webdav.ConnectionError, err:
            exc = errors.CouldNotConnect(_(u"Unable to connect to server: %(error)s") % {'error': err})
            if callback:
                return callMethodInUIThread(callback, (exc, self.itsUUID, None))
            else:
                raise exc

        except M2Crypto.BIO.BIOError, err:
            exc = errors.CouldNotConnect(_(u"Unable to connect to server: %(error)s") % {'error': err})
            if callback:
                return callMethodInUIThread(callback, (exc, self.itsUUID, None))
            else:
                raise exc

        if resp.status != 200:
            exc = errors.SharingError("%s (HTTP status %d)" % (resp.message,
                resp.status),
                details="Received [%s]" % resp.body)
            if callback:
                return callMethodInUIThread(callback, (exc, self.itsUUID, None))
            else:
                raise exc


        info = []

        rootElement = fromstring(resp.body)
        for colElement in rootElement:
            uuid = colElement.get("uuid")
            href = colElement.get("href")
            name = _(u"Untitled")
            tickets = []
            for subElement in colElement:
                if subElement.tag == "{%s}name" % mcURI:
                    name = subElement.text
                elif subElement.tag == "{%s}ticket" % mcURI:
                    ticket = subElement.text
                    ticketType = subElement.get("type")
                    tickets.append( (ticket, ticketType) )

            subscribed = False
            for conduit in getattr(self, 'conduits', []):
                if hasattr(conduit, 'share'):
                    collection = conduit.share.contents
                    if (collection is not None and
                        collection.itsUUID.str16() == uuid):
                        # Already subscribed
                        if uuid in self.unsubscribed:
                            self.unsubscribed.remove(uuid)
                        subscribed = True
                        break
            else:
                # Not subscribed to this collection
                if uuid not in self.ignored and uuid not in self.requested:
                    if uuid not in self.unsubscribed:
                        self.unsubscribed.add(uuid)

            info.append((name, uuid, href, tickets, subscribed))

        if callback:
            return callMethodInUIThread(callback, (None, self.itsUUID, info))

        return info

    def ignoreUnsubscribed(self):
        for uuid in list(self.unsubscribed):
            self.unsubscribed.remove(uuid)
            self.ignored.add(uuid)

    def restoreCollections(self, activity=None):
        rv = self.itsView

        if not self.isSetUp():
            return

        info = self.getPublishedShares(blocking=True)
        toRestore = list()
        for name, uuid, href, tickets, subscribed in info:
            if not subscribed and uuid in self.requested:
                toRestore.append((name, uuid, href, tickets))

        for name, uuid, href, tickets in toRestore:

                try:
                    msg = _("Restoring %(collection)s collection") % {
                        'collection' : name }
                    logger.info(msg)

                    subActivity = Activity(msg)
                    subActivity.started()

                    activity.update(msg=msg, work=1)

                    altView = viewpool.getView(rv.repository)
                    share = Share(itsView=altView, displayName=name)
                    share.mode = 'both'
                    share.conduit = CosmoConduit(itsParent=share,
                        shareName=uuid, account=altView.findUUID(self.itsUUID),
                        translator=translator.SharingTranslator,
                        serializer=eimml.EIMMLSerializer)
                    for ticket, ticketType in tickets:
                        if ticketType == 'read-only':
                            share.conduit.ticketReadOnly = ticket
                        elif ticketType == 'read-write':
                            share.conduit.ticketReadWrite = ticket

                    share.conduit.filters = set()
                    share.conduit.filters.add('cid:reminders-filter@osaf.us')
                    share.conduit.filters.add('cid:needs-reply-filter@osaf.us')
                    share.conduit.filters.add('cid:bcc-filter@osaf.us')

                    share.get(activity=subActivity)
                    if uuid in self.ignored:
                        self.ignored.remove(uuid)
                    self.requested.remove(uuid)
                    share.sharer = schema.ns("osaf.pim",
                        altView).currentContact.item
                    schema.ns("osaf.app",
                        altView).sidebarCollection.add(share.contents)

                    altView.commit(utility.mergeFunction)
                    subActivity.completed()

                except Exception, e:
                    altView.cancel()
                    viewpool.releaseView(altView)
                    if not isinstance(e, ActivityAborted):
                        subActivity.failed(e)
                        activity.failed(e)
                        logger.exception("Restore failed")
                    self.requested.remove(uuid)
                    raise




    @classmethod
    def iterAccounts(cls, rv):
        uuids = [account.itsUUID for account in CosmoAccount.iterItems(rv)]
        for uuid in uuids:
            account = rv.findUUID(uuid)
            if account is not None:
                yield account

    @classmethod
    def ignoreCollection(cls, collection):
        rv = collection.itsView
        for account in CosmoAccount.iterAccounts(rv):
            account.ignored.add(collection.itsUUID.str16())


class HubAccount(CosmoAccount):
    host = schema.One(schema.Text, initialValue="hub.chandlerproject.org")
    path = schema.One(schema.Text, initialValue="/")
    port = schema.One(schema.Integer, initialValue=443)
    useSSL = schema.One(schema.Boolean, initialValue=True)
    accountType = schema.One(schema.Text, initialValue='SHARING_HUB')



class CosmoConduit(recordset_conduit.DiffRecordSetConduit, conduits.HTTPMixin):

    morsecodePath = schema.One(
        schema.Text,
        doc = 'Base path on the host to use for morsecode publishing when '
              'not using an account; sharePath is the user-facing path',
        initialValue = u'',
    )

    chunkSize = schema.One(schema.Integer, defaultValue=100,
        doc="How many items to send at once")

    def sync(self, modeOverride=None, activity=None, forceUpdate=None,
        debug=False):

        startTime = time.time()
        self.networkTime = 0.0

        stats = super(CosmoConduit, self).sync(modeOverride=modeOverride,
            activity=activity, forceUpdate=forceUpdate,
            debug=debug)

        endTime = time.time()
        duration = endTime - startTime
        logger.info("Sync took %6.2f seconds (network = %6.2f)", duration,
            self.networkTime)

        return stats

    def _putChunk(self, chunk, extra):
        text = self.serializer.serialize(self.itsView, chunk, **extra)
        logger.debug("Sending to server [%s]", text)
        self.put(text)

    def putRecords(self, toSend, extra, debug=False, activity=None):

        # If not chunking, send the whole thing.  Also, if toSend is an empty
        # dict, we still want to send to the server in order to create an
        # empty collection (hence the "or not toSend"):
        if self.chunkSize == 0 or not toSend:
            self._putChunk(toSend, extra)
        else:
            # We need to guarantee that masters are sent before modifications,
            # so sorting on uuid/recurrenceID:
            uuids = toSend.keys()
            uuids.sort()

            numUuids = len(uuids)
            numChunks = numUuids / self.chunkSize
            if numUuids % self.chunkSize:
                numChunks += 1
            if activity:
                activity.update(totalWork=numChunks, workDone=0)

            chunk = {}
            chunkNum = 1
            count = 0
            for uuid in uuids:
                count += 1
                chunk[uuid] = toSend[uuid]
                if count == self.chunkSize:
                    if activity:
                        activity.update(msg="Sending chunk %d of %d" %
                            (chunkNum, numChunks))
                    self._putChunk(chunk, extra)
                    if activity:
                        activity.update(msg="Sent chunk %d of %d" %
                            (chunkNum, numChunks), work=1)
                    chunk = {}
                    count = 0
                    chunkNum += 1
            if chunk: # still have some left over
                if activity:
                    activity.update(msg="Sending chunk %d of %d" %
                        (chunkNum, numChunks))
                self._putChunk(chunk, extra)
                if activity:
                    activity.update(msg="Sent chunk %d of %d" %
                        (chunkNum, numChunks), work=1)



    def get(self):

        path = self.getMorsecodePath()

        resp = self._send('GET', path)
        if resp.status == 401:
            raise errors.NotAllowed(
                _(u"Please verify your username and password"),
                details="Received [%s]" % resp.body)

        elif resp.status != 200:
            raise errors.SharingError("%s (HTTP status %d)" % (resp.message,
                resp.status),
                details="Received [%s]" % resp.body)

        syncTokenHeaders = resp.headers.getHeader('X-MorseCode-SyncToken')
        if syncTokenHeaders:
            self.syncToken = syncTokenHeaders[0]
        # # @@@MOR what if this header is missing?

        ticketTypeHeaders = resp.headers.getHeader('X-MorseCode-TicketType')
        if ticketTypeHeaders:
            ticketType = ticketTypeHeaders[0]
            if ticketType == 'read-write':
                self.share.mode = 'both'
            elif ticketType == 'read-only':
                self.share.mode = 'get'

        return resp.body

    def put(self, text):
        path = self.getMorsecodePath()

        if self.syncToken:
            method = 'POST'
        else:
            method = 'PUT'

        tries = 3
        resp = self._send(method, path, text)
        while resp.status == 503:
            tries -= 1
            if tries == 0:
                msg = _(u"Server busy.  Try again later. (HTTP status 503)")
                raise errors.SharingError(msg)
            resp = self._send(method, path, text)

        if resp.status in (205, 423):
            # The collection has either been updated by someone else since
            # we last did a GET (205) or the collection is in the process of
            # being updated right now and is locked (423).  In each case, our
            # reaction is the same -- abort the sync.
            # TODO: We should try to sync again soon
            raise errors.TokenMismatch(_(u"Collection updated by someone else."))

        elif resp.status in (403, 409):
            # Either a collection already exists with the UUID or we've got
            # multiple items with the same icaluid.  Need to parse the response
            # body to find out
            try:
                rootElement = fromstring(resp.body)
            except:
                logger.exception("Couldn't parse response: %s", resp.body)
                rootElement = None
                # continue on

            if (rootElement is not None and
                rootElement.tag == "{%s}error" % mcURI):
                for errorsElement in rootElement:
                    if errorsElement.tag == "{%s}no-uid-conflict" % mcURI:
                        uuids = list()
                        for errorElement in errorsElement:
                            uuids.append(errorElement.text)
                        toRaise = errors.DuplicateIcalUids(
                            _(u"Duplicate ical UIDs detected: %(ids)s") %
                            { 'ids' : ", ".join(uuids) })
                        toRaise.uuids = uuids
                        raise toRaise
            else:
                # not sure what we got back, assume dupe collection uuid
                pass

            # Find out if it's ours:
            shares = self.account.getPublishedShares(blocking=True)
            toRaise = errors.AlreadyExists("%s (HTTP status %d)" %
                (resp.message, resp.status),
                details="Collection already exists on server")
            toRaise.mine = False
            for name, uuid, href, tickets, unsubscribed in shares:
                if uuid == self.share.contents.itsUUID.str16():
                    toRaise.mine = True
            raise toRaise

        elif resp.status == 401:
            raise errors.NotAllowed(
                _(u"Please verify your username and password"),
                details="Received [%s]" % resp.body)

        elif resp.status not in (201, 204):
            raise errors.SharingError("%s (HTTP status %d)" % (resp.message,
                resp.status),
                details="Sent [%s], Received [%s]" % (text, resp.body))

        syncTokenHeaders = resp.headers.getHeader('X-MorseCode-SyncToken')
        if syncTokenHeaders:
            self.syncToken = syncTokenHeaders[0]
        # # @@@MOR what if this header is missing?

        if method == 'PUT':
            ticketHeaders = resp.headers.getHeader('X-MorseCode-Ticket')
            if ticketHeaders:
                for ticketHeader in ticketHeaders:
                    mode, ticket = ticketHeader.split('=')
                    if mode == 'read-only':
                        self.ticketReadOnly = ticket
                    if mode == 'read-write':
                        self.ticketReadWrite = ticket
            if not self.ticketReadOnly or not self.ticketReadWrite:
                raise errors.SharingError("Tickets not returned from server")


    def destroy(self, silent=False):
        path = self.getMorsecodePath()
        resp = self._send('DELETE', path)
        if not silent:
            if resp.status == 404:
                raise errors.NotFound("Collection not found at %s" %
                    path)
            elif resp.status != 204:
                raise errors.SharingError("%s (HTTP status %d)" %
                    (resp.message, resp.status),
                    details="Received [%s]" % resp.body)

    def create(self):
        pass

    def _send(self, methodName, path, body=None):
        # Caller must check resp.status themselves

        handle = self._getServerHandle()

        extraHeaders = { }

        ticket = getattr(self, 'ticket', None)
        if ticket:
            extraHeaders['Ticket'] = ticket

        if self._allTickets:
            extraHeaders['X-MorseCode-Ticket'] = list(self._allTickets)

        syncToken = getattr(self, 'syncToken', None)
        if syncToken:
            extraHeaders['X-MorseCode-SyncToken'] = syncToken

        extraHeaders['Content-Type'] = 'application/eim+xml'

        if methodName == 'PUT':
            extraHeaders['X-MorseCode-TicketType'] = 'read-only read-write'

        request = zanshin.http.Request(methodName, path, extraHeaders, body)

        try:
            start = time.time()
            response = handle.blockUntil(handle.addRequest, request)
            end = time.time()
            if hasattr(self, 'networkTime'):
                self.networkTime += (end - start)
            return response

        except zanshin.webdav.ConnectionError, err:
            raise errors.CouldNotConnect(_(u"Unable to connect to server: %(error)s") % {'error': err})

        except M2Crypto.BIO.BIOError, err:
            raise errors.CouldNotConnect(_(u"Unable to connect to server: %(error)s") % {'error': err})

        except twisted.internet.error.ConnectionLost, err:
            raise errors.CouldNotConnect(_(u"Lost connection to server: %(error)s") % {'error' : err})

    def getLocation(self, privilege=None, morsecode=False):
        """
        Return the user-facing url of the share
        """

        if morsecode:
            f = self._getMorsecodeSettings
        else:
            f = self._getSettings

        (host, port, path, username, password, useSSL) = f(withPassword=False)

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

    def _getSettings(self, withPassword=True):
        password = None
        if self.account is None:
            if withPassword:
                password = getattr(self, "password", None)
                if password:
                    password = waitForDeferred(password.decryptPassword())
            return (self.host, self.port, self.sharePath.strip("/"),
                    self.username, password, self.useSSL)
        else:
            if withPassword:
                password = getattr(self.account, "password", None)
                if password:
                    password = waitForDeferred(password.decryptPassword())
            path = self.account.path.strip("/") + "/" + self.account.pimPath
            return (self.account.host, self.account.port,
                    path.strip("/"),
                    self.account.username,
                    password,
                    self.account.useSSL)



    def getMorsecodePath(self, privilege=None):
        """
        Return the morsecode path of the share
        """

        path = self._getMorsecodeSettings(withPassword=False)[2]
        if path:
            path = "/" + path
        if self.shareName:
            path = "%s/%s" % (path, self.shareName)

        return path


    def _getMorsecodeSettings(self, withPassword=True):
        password = None
        if self.account is None:
            if withPassword:
                password = getattr(self, "password", None)
                if password:
                    password = waitForDeferred(password.decryptPassword())
            return (self.host, self.port, self.morsecodePath.strip("/"),
                    self.username, password, self.useSSL)
        else:
            if withPassword:
                password = getattr(self.account, "password", None)
                if password:
                    password = waitForDeferred(password.decryptPassword())
            path = self.account.path.strip("/") + "/" + self.account.morsecodePath
            return (self.account.host, self.account.port,
                    path.strip("/"),
                    self.account.username,
                    password,
                    self.account.useSSL)


    def getFilter(self):
        # This is where we can filter out things we don't want to send to
        # Cosmo
        filter = super(CosmoConduit, self).getFilter()
        filter += eim.lookupSchemaURI('cid:read-filter@osaf.us')
        filter += eim.lookupSchemaURI('cid:non-standard-ical-filter@osaf.us')
        filter += eim.lookupSchemaURI('cid:mimeContent-filter@osaf.us')
        filter += eim.lookupSchemaURI('cid:rfc2822Message-filter@osaf.us')
        filter += eim.lookupSchemaURI('cid:previousSender-filter@osaf.us')
        filter += eim.lookupSchemaURI('cid:replyToAddress-filter@osaf.us')
        filter += eim.lookupSchemaURI('cid:messageState-filter@osaf.us')
        return filter
