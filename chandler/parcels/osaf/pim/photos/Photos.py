__revision__  = "$Revision: 5958 $"
__date__      = "$Date: 2005-07-12 11:17:39 -0700 (Tue, 12 Jul 2005) $"
__copyright__ = "Copyright (c) 2003-2005 Open Source Applications Foundation"
__license__   = "http://osafoundation.org/Chandler_0.1_license_terms.htm"
__parcel__ = "osaf.pim.photos"

import urllib, time, datetime, cStringIO, logging, mimetypes
import osaf.pim.items as items
from osaf.pim.notes import Note
import osaf.mail.utils as utils
from repository.util.URL import URL
from repository.util.Streams import BlockInputStream
from application import schema
import EXIF

logger = logging.getLogger(__name__)

class PhotoMixin(items.ContentItem):
    schema.kindInfo(displayName="Photo Mixin Kind",
                    displayAttribute="displayName")
    dateTaken = schema.One(schema.DateTime, displayName="taken")
    file = schema.One(schema.String)
    exif = schema.Mapping(schema.String, initialValue={})
    photoBody = schema.One(schema.Lob)

    about = schema.One(redirectTo = 'displayName')
    date = schema.One(redirectTo = 'dateTaken')
    who = schema.One(redirectTo = 'creator')

    schema.addClouds(sharing = schema.Cloud(dateTaken, photoBody))

    def importFromFile(self, path):
        data = file(path, "rb").read()
        (mimeType, encoding) = mimetypes.guess_type(path)
        self.photoBody = utils.dataToBinary(self, 'photoBody', data,
                                            mimeType=mimeType)

    def importFromURL(self, url):
        if isinstance(url, URL):
            url = str(url)
        data = urllib.urlopen(url).read()
        (mimeType, encoding) = mimetypes.guess_type(url)
        self.photoBody = utils.dataToBinary(self, 'photoBody', data,
                                            mimeType=mimeType)

    def exportToFile(self, path):
        data = utils.binaryToData(self.photoBody)
        out = file(path, "wb")
        out.write(data)
        out.close()

    def processEXIF(self):
        input = self.photoBody.getInputStream()
        data = input.read()
        input.close()
        stream = cStringIO.StringIO(data)
        try:
            exif = EXIF.process_file(stream)

            # Warning, serious nesting ahead
            self.dateTaken = datetime.datetime.fromtimestamp(time.mktime(time.strptime(str(exif['Image DateTime']), "%Y:%m:%d %H:%M:%S")))

            self.exif = {}
            for (key, value) in exif.iteritems():
                if isinstance(value, EXIF.IFD_Tag):
                    self.exif[key] = value.printable
                else:
                    self.exif[key] = value

        except Exception, e:
            logger.debug("Couldn't process EXIF of Photo %s (%s)" % \
                (self.itsPath, e))

    def onValueChanged(self, attribute):
        if attribute == "photoBody":
            self.processEXIF()


class Photo(PhotoMixin, Note):
    schema.kindInfo(displayName = "Photo")
