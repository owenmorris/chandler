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

import conduits, errors, formats
from i18n import ChandlerMessageFactory as _
import logging

logger = logging.getLogger(__name__)

shareDict = { }

class InMemoryConduit(conduits.LinkableConduit, conduits.ManifestEngineMixin):
    """ A test conduit, storing data in a dictionary """

    def getLocation(self):
        return self.shareName

    def exists(self):
        return shareDict.has_key(self.shareName)

    def create(self):
        super(InMemoryConduit, self).create()

        if self.exists():
            raise errors.AlreadyExists(_(u"Share already exists"))

        style = self.share.fileStyle()
        if style == formats.STYLE_DIRECTORY:
            shareDict[self.shareName] = { }
        # Nothing to do if style is SINGLE

    def destroy(self):
        super(InMemoryConduit, self).destroy()

        if not self.exists():
            raise errors.NotFound(_(u"Share does not exist"))

        del shareDict[self.shareName]


    def _getResourceList(self, location):
        fileList = { }

        style = self.share.fileStyle()
        if style == formats.STYLE_DIRECTORY:
            for (key, val) in shareDict[self.shareName].iteritems():
                logger.debug("'remote' resource key (%s) (%s)", key, val[0])
                fileList[key] = { 'data' : val[0] }

        return fileList

    def _putItem(self, item):
        path = self._getItemPath(item)

        try:
            text = self.share.format.exportProcess(item)
        except Exception, e:
            logging.exception(e)
            raise errors.TransformationFailed(_(u"Transformation error: see chandler.log for more information"))

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

    def _getItem(self, contentView, itemPath, into=None, activity=None,
                 stats=None):

        text = shareDict[self.shareName][itemPath][1]
        logger.debug("Getting text %s" % text)

        try:
            item = self.share.format.importProcess(contentView, text,
                item=into, activity=activity, stats=stats)
        except errors.MalformedData:
            logger.exception("Failed to parse resource for item %s: '%s'" %
                (itemPath, text.encode('utf8', 'replace')))
            raise

        return (item, shareDict[self.shareName][itemPath][0])


    def _deleteItem(self, itemPath):
        if shareDict[self.shareName].has_key(itemPath):
            del shareDict[self.shareName][itemPath]

    def inject(self, path, text):
        if shareDict[self.shareName].has_key(path):
            etag = shareDict[self.shareName][path][0]
            etag += 1
        else:
            etag = 0

        shareDict[self.shareName][path] = (etag, text)

