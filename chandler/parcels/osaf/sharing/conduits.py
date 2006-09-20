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


__all__ = [
    'InMemoryConduit',
]

import Sharing
import logging
from i18n import ChandlerMessageFactory as _

logger = logging.getLogger(__name__)

shareDict = { }

class InMemoryConduit(Sharing.ShareConduit):
    """ A test conduit, storing data in a dictionary """

    def __init__(self, *args, **kw):
        super(InMemoryConduit, self).__init__(*args, **kw)

        # self.shareDict = kw['shareDict'] # The dictionary to store shares into
        self.shareName = kw['shareName'] # The name of share within dictionary

    def getLocation(self):
        return self.shareName

    def exists(self):
        return shareDict.has_key(self.shareName)

    def create(self):
        super(InMemoryConduit, self).create()

        if self.exists():
            raise sharing.AlreadyExists(_(u"Share already exists"))

        style = self.share.format.fileStyle()
        if style == Sharing.ImportExportFormat.STYLE_DIRECTORY:
            shareDict[self.shareName] = { }
        # Nothing to do if style is SINGLE

    def destroy(self):
        super(InMemoryConduit, self).destroy()

        if not self.exists():
            raise NotFound(_(u"Share does not exist"))

        del shareDict[self.shareName]


    def _getResourceList(self, location):
        fileList = { }

        style = self.share.format.fileStyle()
        if style == Sharing.ImportExportFormat.STYLE_DIRECTORY:
            for (key, val) in shareDict[self.shareName].iteritems():
                fileList[key] = { 'data' : val[0] }

        return fileList

    def _putItem(self, item):
        path = self._getItemPath(item)

        try:
            text = self.share.format.exportProcess(item)
        except Exception, e:
            logging.exception(e)
            raise Sharing.TransformationFailed(_(u"Transformation error: see chandler.log for more information"))

        if text is None:
            return None

        if shareDict[self.shareName].has_key(path):
            etag = shareDict[self.shareName][path][0]
            etag += 1
        else:
            etag = 0

        logger.debug("Putting text %s" % text)

        shareDict[self.shareName][path] = (etag, text)

        return etag

    def _getItem(self, contentView, itemPath, into=None, updateCallback=None,
                 stats=None):

        view = self.itsView
        text = shareDict[self.shareName][itemPath][1]
        logger.debug("Getting text %s" % text)

        try:
            item = self.share.format.importProcess(contentView, text,
                item=into, updateCallback=updateCallback, stats=stats)
        except Sharing.MalformedData:
            logger.exception("Failed to parse resource for item %s: '%s'" %
                (itemPath, text.encode('utf8', 'replace')))
            raise

        return (item, shareDict[self.shareName][itemPath][0])


    def _deleteItem(self, itemPath):
        if shareDict[self.shareName].has_key(itemPath):
            del shareDict[self.shareName][itemPath]
