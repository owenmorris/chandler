#   Copyright (c) 2004-2006 Open Source Applications Foundation
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
    'WebDAVConduit',
]

import conduits, errors, formats
import zanshin, M2Crypto.BIO, twisted.web.http, urlparse
from i18n import ChandlerMessageFactory as _
import logging

logger = logging.getLogger(__name__)

# = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = =

class WebDAVConduit(conduits.LinkableConduit, conduits.ManifestEngineMixin,
    conduits.HTTPMixin):

    def _getSharePath(self):
        return "/" + self._getSettings()[2]

    def _resourceFromPath(self, path):
        serverHandle = self._getServerHandle()
        sharePath = self._getSharePath()

        if sharePath == u"/":
            sharePath = u"" # Avoid double-slashes on next line...
        resourcePath = u"%s/%s" % (sharePath, self.shareName)

        if self.share.format.fileStyle() == formats.STYLE_DIRECTORY:
            resourcePath += "/" + path

        resource = serverHandle.getResource(resourcePath)

        if getattr(self, 'ticket', False):
            resource.ticketId = self.ticket
        return resource

    def exists(self):
        result = super(WebDAVConduit, self).exists()

        resource = self._resourceFromPath(u"")

        try:

            result = self._getServerHandle().blockUntil(resource.exists)
        except zanshin.error.ConnectionError, err:
            raise errors.CouldNotConnect(_(u"Unable to connect to server. Received the following error: %(error)s") % {'error': err.args[0]})
        except M2Crypto.BIO.BIOError, err:
            raise errors.CouldNotConnect(_(u"Unable to connect to server. Received the following error: %(error)s") % {'error': err})
        except zanshin.webdav.PermissionsError, err:
            message = _(u"Not authorized to PUT %(info)s") % {'info': self.getLocation()}
            logger.exception(err)
            raise errors.NotAllowed(message)

        return result

    def _createCollectionResource(self, handle, resource, childName):
        return handle.blockUntil(resource.createCollection, childName)

    def create(self):
        super(WebDAVConduit, self).create()

        style = self.share.format.fileStyle()

        if style == formats.STYLE_DIRECTORY:
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
                raise errors.CouldNotConnect(_(u"Unable to connect to server. Received the following error: %(error)s") % {'error': err})
            except M2Crypto.BIO.BIOError, err:
                raise errors.CouldNotConnect(_(u"Unable to connect to server. Received the following error: %(error)s") % {'error': err})
            except zanshin.http.HTTPError, err:
                logger.error('Received status %d attempting to create %s',
                             err.status, self.getLocation())

                if err.status == twisted.web.http.NOT_ALLOWED:
                    # already exists
                    message = _(u"Collection at %(url)s already exists") % {'url': url}
                    raise errors.AlreadyExists(message)

                if err.status == twisted.web.http.UNAUTHORIZED:
                    # not authorized
                    message = _(u"Not authorized to create collection %(url)s") % {'url': url}
                    raise errors.NotAllowed(message)

                if err.status == twisted.web.http.CONFLICT:
                    # this happens if you try to create a collection within a
                    # nonexistent collection
                    (host, port, sharePath, username, password, useSSL) = \
                        self._getSettings()
                    message = _(u"The directory '%(directoryName)s' could not be found on %(server)s.\nPlease verify the Path setting in your %(accountType)s account") % {'directoryName': sharePath, 'server': host,
                                                        'accountType': 'WebDAV'}
                    raise errors.NotFound(message)

                if err.status == twisted.web.http.FORBIDDEN:
                    # the server doesn't allow the creation of a collection here
                    message = _(u"Server doesn't allow the creation of collections at %(url)s") % {'url': url}
                    raise errors.IllegalOperation(message)

                if err.status == twisted.web.http.PRECONDITION_FAILED:
                    message = _(u"The contents of %(url)s were modified unexpectedly on the server while trying to share.") % {'url':url}
                    raise errors.IllegalOperation(message)

                if err.status != twisted.web.http.CREATED:
                     message = _(u"WebDAV error, status = %(statusCode)d") % {'statusCode': err.status}
                     raise errors.IllegalOperation(message)

    def destroy(self):
        if self.exists():
            self._deleteItem(u"")

    def open(self):
        super(WebDAVConduit, self).open()

    def _getContainerResource(self):

        serverHandle = self._getServerHandle()

        style = self.share.format.fileStyle()

        if style == formats.STYLE_DIRECTORY:
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

    def _putItem(self, item):
        """
        putItem should publish an item and return etag/date, etc.
        """

        try:
            text = self.share.format.exportProcess(item)
        except:
            logger.exception("Failed to export item")
            msg = _(u"Transformation failed for %(item)s") % {'item': item}
            raise errors.TransformationFailed(msg)

        if text is None:
            return None

        contentType = self.share.format.contentType(item)
        itemName = self._getItemPath(item)
        container = self._getContainerResource()

        try:
            # @@@MOR For some reason, when doing a PUT on the rpi server, I
            # can see it's returning 400 Bad Request, but zanshin doesn't
            # seem to be raising an exception.  Putting in a check for
            # newResource == None as another indicator that it failed to
            # create the resource
            newResource = None
            serverHandle = self._getServerHandle()

            # Here, if the resource doesn't exist on the server, we're
            # going to call container.createFile(), which will fail
            # with a 412 (PRECONDITION_FAILED) iff something already
            # exists at that location.
            #
            # If the resource does exist, we get hold of it, and
            # call resource.put(), which fails with a 412 iff the
            # etag of the resource changed.

            ## if not self.resourceList.has_key(itemName):
            ##     newResource = serverHandle.blockUntil(
            ##                       container.createFile, itemName, body=text,
            ##                       type=contentType)
            ## else:
            resourcePath = container.path + itemName
            resource = serverHandle.getResource(resourcePath)

            if getattr(self, 'ticket', False):
                resource.ticketId = self.ticket

            serverHandle.blockUntil(resource.put, text, checkETag=False,
                                    contentType=contentType)

            # We're using newResource of None to track errors
            newResource = resource

        except zanshin.webdav.ConnectionError, err:
            raise errors.CouldNotConnect(_(u"Unable to connect to server. Received the following error: %(error)s") % {'error': err})
        except M2Crypto.BIO.BIOError, err:
            raise errors.CouldNotConnect(_(u"Unable to connect to server. Received the following error: %(error)s") % {'error': err})
        # 201 = new, 204 = overwrite

        except zanshin.webdav.PermissionsError:
            message = _(u"Not authorized to PUT %(info)s") % {'info': itemName}
            raise errors.NotAllowed(message)

        except zanshin.webdav.WebDAVError, err:

            if err.status in (twisted.web.http.FORBIDDEN,
                              twisted.web.http.CONFLICT,
                              twisted.web.http.PRECONDITION_FAILED):
                # [@@@] grant: Should probably come up with a better message
                # for PRECONDITION_FAILED (an ETag conflict).
                # seen if trying to PUT to a nonexistent collection (@@@MOR verify)
                message = _(u"Publishing %(itemName)s failed; server rejected our request with status %(status)d") % {'itemName': itemName, 'status': err.status}
                raise errors.NotAllowed(message)

        if newResource is None:
            message = _(u"Not authorized to PUT %(itemName)s %(body)s") % {'itemName': itemName, 'body' : text}
            raise errors.NotAllowed(message)

        etag = newResource.etag

        # @@@ [grant] Get mod-date?
        return etag

    def _deleteItem(self, itemPath):
        resource = self._resourceFromPath(itemPath)
        logger.info("...removing from server: %s" % resource.path)

        if resource != None:
            try:
                deleteResp = self._getServerHandle().blockUntil(resource.delete)
            except zanshin.webdav.ConnectionError, err:
                raise errors.CouldNotConnect(_(u"Unable to connect to server. Received the following error: %(error)s") % {'error': err})
            except M2Crypto.BIO.BIOError, err:
                raise errors.CouldNotConnect(_(u"Unable to connect to server. Received the following error: %(error)s") % {'error': err})

    def _getItem(self, contentView, itemPath, into=None, updateCallback=None,
                 stats=None):

        view = self.itsView
        resource = self._resourceFromPath(itemPath)

        try:
            resp = self._getServerHandle().blockUntil(resource.get)

        except zanshin.webdav.ConnectionError, err:
            raise errors.CouldNotConnect(_(u"Unable to connect to server. Received the following error: %(error)s") % {'error': err})
        except M2Crypto.BIO.BIOError, err:
            raise errors.CouldNotConnect(_(u"Unable to connect to server. Received the following error: %(error)s") % {'error': err})

        if resp.status == twisted.web.http.NOT_FOUND:
            message = _(u"Path %(path)s not found") % {'path': resource.path}
            raise errors.NotFound(message)

        if resp.status == twisted.web.http.UNAUTHORIZED:
            message = _(u"Not authorized to GET %(path)s") % {'path': resource.path}
            raise errors.NotAllowed(message)

        text = resp.body

        etag = resource.etag

        try:
            item = self.share.format.importProcess(contentView, text,
                item=into, updateCallback=updateCallback, stats=stats)

        except errors.MalformedData:
            logger.exception("Failed to parse resource for item %s: '%s'" %
                (itemPath, text.encode('utf8', 'replace')))
            raise

        return (item, etag)


    def _getResourceList(self, location): # must implement
        """
        Return information (etags) about all resources within a collection
        """

        resourceList = {}

        style = self.share.format.fileStyle()
        if style == formats.STYLE_DIRECTORY:
            shareCollection = self._getContainerResource()

            try:
                children = self._getServerHandle().blockUntil(
                                shareCollection.getAllChildren)

            except zanshin.webdav.ConnectionError, err:
                raise errors.CouldNotConnect(_(u"Unable to connect to server. Received the following error: %(error)s") % {'error': err})
            except M2Crypto.BIO.BIOError, err:
                raise errors.CouldNotConnect(_(u"Unable to connect to server. Received the following error: %(error)s") % {'error': err})
            except zanshin.webdav.WebDAVError, e:

                if e.status == twisted.web.http.NOT_FOUND:
                    raise errors.NotFound(_(u"Path %(path)s not found") % {'path': shareCollection.path})

                if e.status == twisted.web.http.UNAUTHORIZED:
                    raise errors.NotAllowed(_(u"Not authorized to get %(path)s") % {'path': shareCollection.path})

                raise errors.SharingError(_(u"The following sharing error occurred: %(error)s") % {'error': e})


            for child in children:
                if child != shareCollection:
                    path = child.path.split("/")[-1]
                    etag = child.etag
                    # if path is empty, it's a subcollection (skip it)
                    if path:
                        resourceList[path] = { 'data' : etag }

        elif style == formats.STYLE_SINGLE:
            resource = self._getServerHandle().getResource(location)
            if getattr(self, 'ticket', False):
                resource.ticketId = self.ticket
            # @@@ [grant] Error handling and reporting here
            # are sub-optimal
            try:
                self._getServerHandle().blockUntil(resource.propfind, depth=0)
            except zanshin.webdav.ConnectionError, err:
                raise errors.CouldNotConnect(_(u"Unable to connect to server. Received the following error: %(error)s") % {'error': err})
            except M2Crypto.BIO.BIOError, err:
                raise errors.CouldNotConnect(_(u"Unable to connect to server. Received the following error: %(error)s") % {'error': err})
            except zanshin.webdav.PermissionsError, err:
                message = _(u"Not authorized to GET %(path)s") % {'path': location}
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

