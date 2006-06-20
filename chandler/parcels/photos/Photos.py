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


__parcel__ = "photos"

import urllib, time, cStringIO, logging, mimetypes
from datetime import datetime
from osaf import pim
from repository.util.URL import URL
from application import schema
import EXIF
from i18n import OSAFMessageFactory as _
from PyICU import ICUtzinfo
from osaf.framework.blocks import NewItemEvent
import application.dialogs.Util
import wx
import os

logger = logging.getLogger(__name__)

class PhotoMixin(pim.ContentItem):
    schema.kindInfo(displayName=u"Photo Mixin Kind",
                    displayAttribute="displayName")
    dateTaken = schema.One(schema.DateTime, displayName=_(u"taken"))
    file = schema.One(schema.Text)
    exif = schema.Mapping(schema.Text, initialValue={})
    photoBody = schema.One(schema.Lob)

    about = schema.One(redirectTo = 'displayName')
    date = schema.One(redirectTo = 'dateTaken')
    who = schema.One(redirectTo = 'creator')

    schema.addClouds(sharing = schema.Cloud(dateTaken, photoBody))

    def importFromFile(self, path):
        if isinstance(path, unicode):
            path = path.encode('utf8')

        data = file(path, "rb").read()
        (mimetype, encoding) = mimetypes.guess_type(path)
        self.photoBody = self.itsView.createLob(data, mimetype=mimetype,
            compression='bz2')

    def importFromURL(self, url):
        if isinstance(url, URL):
            url = str(url)
        data = urllib.urlopen(url).read()
        (mimetype, encoding) = mimetypes.guess_type(url)
        self.photoBody = self.itsView.createLob(data, mimetype=mimetype,
            compression='bz2')

    def exportToFile(self, path):
        if isinstance(path, unicode):
            path = path.encode('utf8')

        input = self.photoBody.getInputStream()
        data = input.read()
        input.close()
        out = file(path, "wb")
        out.write(data)
        out.close()

    def processEXIF(self):
        if hasattr(self, 'photoBody'):
            input = self.photoBody.getInputStream()
        else:
            input = file(self.file, 'r')

        data = input.read()
        input.close()
        stream = cStringIO.StringIO(data)
        try:
            exif = EXIF.process_file(stream)

            # First try DateTimeOriginal, falling back to DateTime
            takenString = str(exif.get('EXIF DateTimeOriginal',
                              exif['Image DateTime']))

            timestamp = time.mktime(time.strptime(takenString,
                "%Y:%m:%d %H:%M:%S"))
            self.dateTaken = datetime.fromtimestamp(timestamp)
            if self.dateTaken.tzinfo is None:
                self.dateTaken = self.dateTaken.replace(tzinfo=ICUtzinfo.default)

            self.exif = {}
            for (key, value) in exif.iteritems():
                if isinstance(value, EXIF.IFD_Tag):
                    self.exif[key] = unicode(value.printable)
                else:
                    self.exif[key] = unicode(value)

        except Exception, e:
            logger.debug("Couldn't process EXIF of Photo %s (%s)" % \
                (self.itsPath, e))

    def onValueChanged(self, attribute):
        if attribute == "photoBody":
            self.processEXIF()


class Photo(PhotoMixin, pim.Note):
    schema.kindInfo(displayName = u"Photo")


class NewImageEvent(NewItemEvent):
    """
    An event used to import a new image from disk.
    """
    def onNewItem (self):
        """
        Called to create a new Photo.
        """
        photo = None
        cmd, dir, filename = application.dialogs.Util.showFileDialog(
            None,
            _(u"Choose an image to import"),
            "",
            "",
            _(u"Images|*.jpg;*.gif;*.png|All files (*.*)|*.*"),
            wx.OPEN
        )

        theApp = wx.GetApp()
        if cmd == wx.ID_OK:
            path = os.path.join(dir, filename)

            # We'll us CallItemMethodAsync, which works from other repository
            # views, since this code should eventually be run in a background
            # thread with a non UI repository view. In the mean time we'll
            # call Yield.
            theApp.CallItemMethodAsync("MainView",
                                       'setStatusMessage',
                                       _(u"Importing %(filePath)s") % {'filePath': path})
            wx.Yield()
            photo = Photo(itsView=self.itsView)
            photo.displayName = filename
            photo.creator = schema.ns("osaf.pim", self.itsView).currentContact.item
            photo.importFromFile(path)
    
        theApp.CallItemMethodAsync("MainView",
                                   'setStatusMessage',
                                   _(u""))
        return photo

