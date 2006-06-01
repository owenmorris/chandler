__copyright__ = "Copyright (c) 2003-2005 Open Source Applications Foundation"
__license__   = "http://osafoundation.org/Chandler_0.1_license_terms.htm"
__parcel__ = "photos"

import urllib, time, cStringIO, logging, mimetypes
from datetime import datetime
from osaf import pim
from repository.util.URL import URL
from repository.util.Streams import BlockInputStream
from application import schema
import EXIF
from i18n import OSAFMessageFactory as _
from PyICU import ICUtzinfo

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
