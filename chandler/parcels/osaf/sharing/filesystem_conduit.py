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
    'FileSystemConduit',
    'FileSystemMonolithicRecordSetConduit',
]

import os
import conduits, formats, errors, recordset_conduit
from i18n import ChandlerMessageFactory as _

import logging
logger = logging.getLogger(__name__)

class FileSystemConduit(conduits.LinkableConduit, conduits.ManifestEngineMixin):

    def getLocation(self, privilege=None):
        if self.hasLocalAttributeValue("sharePath") and \
         self.hasLocalAttributeValue("shareName"):
            return os.path.join(self.sharePath, self.shareName)
        raise errors.Misconfigured(_(u"A misconfiguration error was encountered"))

    def _get(self, contentView, resourceList, activity=None,
             getPhrase=None):
        if getPhrase is None:
            getPhrase = _(u"Importing from %(name)s...")
        return super(FileSystemConduit, self)._get(contentView,
            resourceList, activity, getPhrase)

    def _putItem(self, item):
        path = self._getItemFullPath(self._getItemPath(item))

        try:
            text = self.share.format.exportProcess(item)
        except:
            logger.exception("Failed to export item")
            raise errors.TransformationFailed(_(u"Transformation error: see chandler.log for more information"))

        if text is None:
            return None
        out = file(path, 'wb') #outputting in binary mode to preserve ics CRLF
        out.write(text)
        out.close()
        stat = os.stat(path)
        return stat.st_mtime

    def _deleteItem(self, itemPath):
        path = self._getItemFullPath(itemPath)

        logger.info("...removing from disk: %s" % path)
        os.remove(path)

    def _getItem(self, contentView, itemPath, into=None, activity=None,
        stats=None):

        # logger.info("Getting item: %s" % itemPath)
        path = self._getItemFullPath(itemPath)

        extension = os.path.splitext(path)[1].strip(os.path.extsep)
        text = file(path).read()

        try:
            item = self.share.format.importProcess(contentView, text,
                extension=extension, item=into,
                activity=activity, stats=stats)

        except errors.MalformedData:
            logger.exception("Failed to parse resource for item %s: '%s'" %
                (itemPath, text.encode('utf8', 'replace')))
            raise

        stat = os.stat(path)
        return (item, stat.st_mtime)

    def _getResourceList(self, location):
        fileList = {}

        style = self.share.fileStyle()
        if style == formats.STYLE_DIRECTORY:
            for filename in os.listdir(location):
                fullPath = os.path.join(location, filename)
                stat = os.stat(fullPath)
                fileList[filename] = { 'data' : stat.st_mtime }

        elif style == formats.STYLE_SINGLE:
            stat = os.stat(location)
            fileList[self.shareName] = { 'data' : stat.st_mtime }

        else:
            print "@@@MOR Raise an exception here"

        return fileList

    def _getItemFullPath(self, path):
        style = self.share.fileStyle()
        if style == formats.STYLE_DIRECTORY:
            path = os.path.join(self.sharePath, self.shareName, path)
        elif style == formats.STYLE_SINGLE:
            path = os.path.join(self.sharePath, self.shareName)
        return path


    def exists(self):
        super(FileSystemConduit, self).exists()

        style = self.share.fileStyle()
        if style == formats.STYLE_DIRECTORY:
            return os.path.isdir(self.getLocation())
        elif style == formats.STYLE_SINGLE:
            return os.path.isfile(self.getLocation())
        else:
            print "@@@MOR Raise an exception here"

    def create(self):
        super(FileSystemConduit, self).create()

        if self.exists():
            raise errors.AlreadyExists(_(u"Share path already exists"))

        if self.sharePath is None or not os.path.isdir(self.sharePath):
            raise errors.Misconfigured(_(u"Share path is not set, or path doesn't exist"))

        style = self.share.fileStyle()
        if style == formats.STYLE_DIRECTORY:
            path = self.getLocation()
            if not os.path.exists(path):
                os.mkdir(path)

    def destroy(self):
        super(FileSystemConduit, self).destroy()

        path = self.getLocation()

        if not self.exists():
            raise errors.NotFound(_(u"%(path)s does not exist") % {'path': path})

        style = self.share.fileStyle()
        if style == formats.STYLE_DIRECTORY:
            for filename in os.listdir(path):
                os.remove(os.path.join(path, filename))
            os.rmdir(path)
        elif style == formats.STYLE_SINGLE:
            os.remove(path)


    def open(self):
        super(FileSystemConduit, self).open()

        path = self.getLocation()

        if not self.exists():
            raise errors.NotFound(_(u"%(path)s does not exist") % {'path': path})






class FileSystemMonolithicRecordSetConduit(
    recordset_conduit.MonolithicRecordSetConduit):


    def _getPath(self):
        return "/".join([self.sharePath, self.shareName])

    def get(self):
        mtime = float(self.etag) if self.etag else 0.0
        path = self._getPath()
        stat = os.stat(path)
        if mtime <= stat.st_mtime:
            text = file(path).read()
            self.etag = str(stat.st_mtime)
        return text

    def put(self, text):
        mtime = float(self.etag) if self.etag else 0.0
        path = self._getPath()
        try:
            stat = os.stat(path)
            lastMod = stat.st_mtime
        except OSError:
            lastMod = 0.0

        if mtime < lastMod:
            raise errors.TokenMismatch("File has been updated")

        # outputting in binary mode to preserve ics CRLF
        out = file(path, 'wb')
        out.write(text)
        out.close()
        stat = os.stat(path)
        self.etag = str(stat.st_mtime)

    def exists(self):
        return os.path.isfile(self._getPath())

    def destroy(self):
        path = self._getPath()
        if not self.exists():
            raise errors.NotFound(_(u"%(path)s does not exist") %
                {'path': path})

        os.remove(path)

    def create(self):
        if self.exists():
            raise errors.AlreadyExists(_(u"File already exists"))
