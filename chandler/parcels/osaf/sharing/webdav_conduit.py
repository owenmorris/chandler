#   Copyright (c) 2004-2007 Open Source Applications Foundation
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
    'WebDAVRecordSetConduit',
    'WebDAVMonolithicRecordSetConduit',
]

import conduits, errors, utility
import zanshin, M2Crypto.BIO, twisted.web.http, urlparse
import twisted.internet.error
from recordset_conduit import (
    ResourceRecordSetConduit, MonolithicRecordSetConduit
)

from i18n import ChandlerMessageFactory as _
import time
import logging

logger = logging.getLogger(__name__)

# = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = =


class DAVConduitMixin(conduits.HTTPMixin):

    def _getSharePath(self):
        return "/" + self._getSettings(withPassword=False)[2]

    def _resourceFromPath(self, path):
        serverHandle = self._getServerHandle()
        sharePath = self._getSharePath()

        if sharePath == u"/":
            sharePath = u"" # Avoid double-slashes on next line...
        resourcePath = u"%s/%s" % (sharePath, self.shareName)

        if self.share.fileStyle() == utility.STYLE_DIRECTORY:
            if not resourcePath.endswith("/"):
                resourcePath += "/"
            resourcePath += path

        resource = serverHandle.getResource(resourcePath)

        if getattr(self, 'ticket', False):
            resource.ticketId = self.ticket
        return resource

    def exists(self):

        resource = self._resourceFromPath(u"")

        try:

            result = self._getServerHandle().blockUntil(resource.exists)
        except zanshin.error.ConnectionError, err:
            raise errors.CouldNotConnect(_(u"Unable to connect to server: %(error)s") % {'error': err.args[0]})
        except M2Crypto.BIO.BIOError, err:
            raise errors.CouldNotConnect(_(u"Unable to connect to server: %(error)s") % {'error': err})
        except zanshin.webdav.PermissionsError, err:
            message = _(u"Not authorized to PUT %(info)s.") % {'info': self.getLocation()}
            logger.exception(err)
            raise errors.NotAllowed(message)

        return result

    def _createCollectionResource(self, handle, resource, childName):
        return handle.blockUntil(resource.createCollection, childName)

    def create(self):

        style = self.share.fileStyle()

        if style == utility.STYLE_DIRECTORY:
            url = self.getLocation()
            handle = self._getServerHandle()
            try:
                if url[-1] != '/': url += '/'

                # need to get resource representing the parent of the
                # collection we want to create

                # Get the parent directory of the given path:
                # '/dev1/foo/bar' becomes ['dev1', 'foo', 'bar']
                path = url.strip('/').split('/')
                parentPath = path[:-1]
                childName = path[-1]
                # ['dev1', 'foo'] becomes "dev1/foo"
                url = "/".join(parentPath)
                resource = handle.getResource(url)
                if getattr(self, 'ticket', False):
                    resource.ticketId = self.ticket

                child = self._createCollectionResource(handle, resource,
                    childName)

            except zanshin.webdav.ConnectionError, err:
                raise errors.CouldNotConnect(_(u"Unable to connect to server: %(error)s") % {'error': err})
            except M2Crypto.BIO.BIOError, err:
                raise errors.CouldNotConnect(_(u"Unable to connect to server: %(error)s") % {'error': err})
            except zanshin.http.HTTPError, err:
                logger.error('Received status %d attempting to create %s',
                             err.status, self.getLocation())

                if err.status == twisted.web.http.NOT_ALLOWED:
                    # already exists
                    message = _(u"Collection at %(url)s already exists.") % {'url': url}
                    raise errors.AlreadyExists(message)

                if err.status == twisted.web.http.UNAUTHORIZED:
                    # not authorized
                    message = _(u"Not authorized to create collection %(url)s.") % {'url': url}
                    raise errors.NotAllowed(message)

                if err.status == twisted.web.http.CONFLICT:
                    # this happens if you try to create a collection within a
                    # nonexistent collection
                    (host, port, sharePath, username, password, useSSL) = \
                        self._getSettings(withPassword=False)
                    message = _(u"The directory '%(directoryName)s' could not be found on %(server)s.\nPlease verify the Path field in your %(accountType)s account.") % {'directoryName': sharePath, 'server': host,
                                                        'accountType': 'WebDAV'}
                    raise errors.NotFound(message)

                if err.status == twisted.web.http.FORBIDDEN:
                    # the server doesn't allow the creation of a collection here
                    message = _(u"Server doesn't allow publishing collections to %(url)s.") % {'url': url}
                    raise errors.IllegalOperation(message)

                if err.status == twisted.web.http.PRECONDITION_FAILED:
                    message = _(u"The contents of %(url)s were modified unexpectedly on the server while trying to publish.") % {'url':url}
                    raise errors.IllegalOperation(message)

                if err.status != twisted.web.http.CREATED:
                     message = _(u"WebDAV error, status = %(statusCode)d") % {'statusCode': err.status}
                     raise errors.IllegalOperation(message)

    def destroy(self):
        if self.exists():
            resource = self._resourceFromPath("")
            logger.info("...removing from server: %s" % resource.path)
            if resource != None:
                try:
                    deleteResp = self._getServerHandle().blockUntil(
                        resource.delete)
                except zanshin.webdav.ConnectionError, err:
                    raise errors.CouldNotConnect(_(u"Unable to connect to server: %(error)s") % {'error': err})
                except M2Crypto.BIO.BIOError, err:
                    raise errors.CouldNotConnect(_(u"Unable to connect to server: %(error)s") % {'error': err})


    def _getContainerResource(self):

        serverHandle = self._getServerHandle()

        style = self.share.fileStyle()

        if style == utility.STYLE_DIRECTORY:
            path = self.getLocation()
        else:
            path = self._getSharePath()

        # Make sure we have a container
        if path and path[-1] != '/':
            path += '/'

        resource = serverHandle.getResource(path)
        if getattr(self, 'ticket', False):
            resource.ticketId = self.ticket
        return resource


    def _getResourceList(self, location): # must implement
        """
        Return information (etags) about all resources within a collection
        """

        resourceList = {}

        style = self.share.fileStyle()
        if style == utility.STYLE_DIRECTORY:
            shareCollection = self._getContainerResource()

            try:
                children = self._getServerHandle().blockUntil(
                                shareCollection.getAllChildren)

            except zanshin.webdav.ConnectionError, err:
                raise errors.CouldNotConnect(_(u"Unable to connect to server: %(error)s") % {'error': err})
            except M2Crypto.BIO.BIOError, err:
                raise errors.CouldNotConnect(_(u"Unable to connect to server: %(error)s") % {'error': err})
            except zanshin.webdav.WebDAVError, e:

                if e.status == twisted.web.http.NOT_FOUND:
                    raise errors.NotFound(_(u"Path %(path)s not found.") % {'path': shareCollection.path})

                if e.status == twisted.web.http.UNAUTHORIZED:
                    raise errors.NotAllowed(_(u"Not authorized to get %(path)s.") % {'path': shareCollection.path})

                raise errors.SharingError(_(u"Sharing Error: %(error)s.") % {'error': e})


            for child in children:
                if child != shareCollection:
                    path = child.path.split("/")[-1]
                    etag = child.etag
                    # if path is empty, it's a subcollection (skip it)
                    if path:
                        resourceList[path] = { 'data' : etag }

        elif style == utility.STYLE_SINGLE:
            resource = self._getServerHandle().getResource(location)
            if getattr(self, 'ticket', False):
                resource.ticketId = self.ticket
            # @@@ [grant] Error handling and reporting here
            # are sub-optimal
            try:
                self._getServerHandle().blockUntil(resource.propfind, depth=0)
            except zanshin.webdav.ConnectionError, err:
                raise errors.CouldNotConnect(_(u"Unable to connect to server: %(error)s") % {'error': err})
            except M2Crypto.BIO.BIOError, err:
                raise errors.CouldNotConnect(_(u"Unable to connect to server: %(error)s") % {'error': err})
            except zanshin.webdav.PermissionsError, err:
                message = _(u"Not authorized to GET %(path)s.") % {'path': location}
                raise errors.NotAllowed(message)
            #else:
                #if not exists:
                #    raise NotFound(_(u"Path %(path)s not found") % {'path': resource.path})
#

            etag = resource.etag
            # @@@ [grant] count use resource.path here
            path = urlparse.urlparse(location)[2]
            path = path.split("/")[-1]
            resourceList[path] = { 'data' : etag }

        return resourceList

    def connect(self):
        self._releaseServerHandle()
        self._getServerHandle() # @@@ [grant] Probably not necessary

    def disconnect(self):
        self._releaseServerHandle()

    def createTickets(self):
        handle = self._getServerHandle()
        location = self.getLocation()
        if not location.endswith("/"):
            location += "/"
        resource = handle.getResource(location)

        ticket = handle.blockUntil(resource.createTicket)
        logger.debug("Read Only ticket: %s %s",
            ticket.ticketId, ticket.ownerUri)
        self.ticketReadOnly = ticket.ticketId

        ticket = handle.blockUntil(resource.createTicket, write=True)
        logger.debug("Read Write ticket: %s %s",
            ticket.ticketId, ticket.ownerUri)
        self.ticketReadWrite = ticket.ticketId

        return (self.ticketReadOnly, self.ticketReadWrite)

    def getTickets(self):
        handle = self._getServerHandle()
        location = self.getLocation()
        if not location.endswith("/"):
            location += "/"
        resource = handle.getResource(location)

        try:
            tickets = handle.blockUntil(resource.getTickets)
            for ticket in tickets:
                if ticket.write:
                    self.ticketReadWrite = ticket.ticketId
                elif ticket.read:
                    self.ticketReadOnly = ticket.ticketId

        except Exception, e:
            # Couldn't get tickets due to permissions problem, or there were
            # no tickets
            pass

    def setDisplayName(self, name):
        handle = self._getServerHandle()
        location = self.getLocation()
        if not location.endswith("/"):
            location += "/"
        resource = handle.getResource(location)
        try:
            handle.blockUntil(resource.setDisplayName, name)
        except zanshin.http.HTTPError:
            # Ignore HTTP errors (like PROPPATCH not being supported)
            pass









class WebDAVRecordSetConduit(ResourceRecordSetConduit, DAVConduitMixin):
    """ Implements the new EIM/RecordSet interface """

    def sync(self, modeOverride=None, activity=None, forceUpdate=None,
        debug=False):

        startTime = time.time()
        self.networkTime = 0.0

        stats = super(WebDAVRecordSetConduit, self).sync(
            modeOverride=modeOverride,
            activity=activity, forceUpdate=forceUpdate,
            debug=debug)

        endTime = time.time()
        duration = endTime - startTime
        logger.info("Sync took %6.2f seconds (network = %6.2f)", duration,
            self.networkTime)

        return stats

    def getResource(self, path):
        # return text, etag
        resource = self._resourceFromPath(path)

        try:
            start = time.time()
            resp = self._getServerHandle().blockUntil(resource.get)
            end = time.time()
            self.networkTime += (end - start)

        except twisted.internet.error.ConnectionDone, err:
            errors.annotate(err, _(u"Server reported incorrect Content-Length for %(itemPath)s.") % \
                            {"itemPath": path}, details=str(err))
            raise
        except zanshin.webdav.ConnectionError, err:
            raise errors.CouldNotConnect(_(u"Unable to connect to server: %(error)s") % {'error': err})
        except M2Crypto.BIO.BIOError, err:
            raise errors.CouldNotConnect(_(u"Unable to connect to server: %(error)s") % {'error': err})

        if resp.status == twisted.web.http.NOT_FOUND:
            message = _(u"Path %(path)s not found.") % {'path': resource.path}
            raise errors.NotFound(message)

        if resp.status in (twisted.web.http.UNAUTHORIZED,
                           twisted.web.http.FORBIDDEN):
            message = _(u"Not authorized to GET %(path)s.") % {'path': resource.path}
            raise errors.NotAllowed(message)

        text = resp.body
        etag = resource.etag.strip('"') # .mac puts quotes around the etag
        return text, etag


    def putResource(self, text, path, etag=None, debug=False):
        # return etag
        resource = self._resourceFromPath(path)
        start = time.time()
        self._getServerHandle().blockUntil(resource.put, text,
            checkETag=False)
        end = time.time()
        self.networkTime += (end - start)
        return resource.etag.strip('"') # .mac puts quotes around the etag



    def deleteResource(self, path, etag=None):
        resource = self._resourceFromPath(path)
        resp = self._getServerHandle().blockUntil(resource.delete)

        if not 200 <= resp.status < 300:
            raise errors.SharingError("%s (HTTP status %d)" % (resp.message,
                resp.status),
                details="Received [%s]" % resp.body)



    def getResources(self):
        # return resources{ path : etag }

        resources = { }
        location = self.getLocation()
        res = self._getResourceList(location)
        for path, data in res.iteritems():
            resources[path] = data['data']

        return resources

    def getPath(self, uuid):
        return "%s.xml" % uuid






class WebDAVMonolithicRecordSetConduit(MonolithicRecordSetConduit,
    DAVConduitMixin):

    def sync(self, modeOverride=None, activity=None, forceUpdate=None,
        debug=False):

        startTime = time.time()
        self.networkTime = 0.0

        stats = super(WebDAVMonolithicRecordSetConduit, self).sync(
            modeOverride=modeOverride,
            activity=activity, forceUpdate=forceUpdate,
            debug=debug)

        endTime = time.time()
        duration = endTime - startTime
        logger.info("Sync took %6.2f seconds (network = %6.2f)", duration,
            self.networkTime)

        return stats


    def get(self):
        handle = self._getServerHandle()

        path = self._getSharePath()
        if path == "/":
            path = ""
        path = "/".join([path, self.shareName])

        if self.etag:
            extraHeaders = { 'If-None-Match' : self.etag }
        else:
            extraHeaders = { }

        start = time.time()
        resp = handle.blockUntil(handle.get, path, extraHeaders=extraHeaders)
        end = time.time()
        self.networkTime += (end - start)

        if resp.status == 304: # Not Modified
            return None

        elif resp.status != 200:
            raise errors.SharingError("%s (HTTP status %d)" % (resp.message,
                resp.status),
                details="Received [%s]" % resp.body)

        text = resp.body

        etag = resp.headers.getHeader('ETag')
        if etag: # etag is a zanshin.http.ETag object
            self.etag = etag.tag

        return text


    def put(self, text):
        handle = self._getServerHandle()

        path = self._getSharePath()
        if path == "/":
            path = ""
        path = "/".join([path, self.shareName])

        if self.etag:
            extraHeaders = { 'If-Match' : self.etag }
        else:
            extraHeaders = { }

        start = time.time()
        resp = handle.blockUntil(handle.put, path, text,
            extraHeaders=extraHeaders)
        end = time.time()
        self.networkTime += (end - start)

        if not (200 <= resp.status < 300):
            raise errors.SharingError("%s (HTTP status %d)" % (resp.message,
                resp.status),
                details="Received [%s]" % resp.body)

        etag = resp.headers.getHeader('ETag')
        if etag: # etag is a zanshin.http.ETag object
            self.etag = etag.tag

