__revision__  = "$Revision: 5958 $"
__date__      = "$Date: 2005-07-12 11:17:39 -0700 (Tue, 12 Jul 2005) $"
__copyright__ = "Copyright (c) 2003-2005 Open Source Applications Foundation"
__license__   = "http://osafoundation.org/Chandler_0.1_license_terms.htm"
__parcel__ = "osaf.contentmodel.photos"

import urllib, time, datetime, cStringIO, logging, mimetypes
import osaf.contentmodel.ContentModel as ContentModel
import osaf.contentmodel.Notes as Notes
import osaf.mail.utils as utils
from repository.util.URL import URL
from repository.util.Streams import BlockInputStream
from application import schema
import EXIF

logger = logging.getLogger('Photos')
logger.setLevel(logging.INFO)

class PhotoMixin(ContentModel.ContentItem):
    schema.kindInfo(displayName="Photo Mixin Kind", displayAttribute="caption")
    caption = schema.One(schema.String, displayName="Caption")
    dateTaken = schema.One(schema.DateTime, displayName="Date Taken")
    data = schema.One(schema.Lob)
    file = schema.One(schema.String)
    exif = schema.Mapping(schema.String, initialValue={})

    about = schema.One(redirectTo = 'caption')
    date = schema.One(redirectTo = 'dateTaken')
    who = schema.One(redirectTo = 'creator')
    displayName = schema.Role(redirectTo="caption")

    schema.addClouds(sharing = schema.Cloud(caption,dateTaken,data))

    def importFromFile(self, path):
        data = file(path, "rb").read()
        (mimeType, encoding) = mimetypes.guess_type(path)
        self.data = utils.dataToBinary(self, 'data', data, mimeType=mimeType)

    def importFromURL(self, url):
        if isinstance(url, URL):
            url = str(url)
        data = urllib.urlopen(url).read()
        (mimeType, encoding) = mimetypes.guess_type(url)
        self.data = utils.dataToBinary(self, 'data', data, mimeType=mimeType)

    def exportToFile(self, path):
        data = utils.binaryToData(self.data)
        out = file(path, "wb")
        out.write(data)
        out.close()

    def processEXIF(self):
        input = self.data.getInputStream()
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
        if attribute == "data":
            self.processEXIF()


class Photo(PhotoMixin, Notes.Note):
    schema.kindInfo(displayName = "Photo")
