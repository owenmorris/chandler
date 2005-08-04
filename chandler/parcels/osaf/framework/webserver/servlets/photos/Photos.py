
from twisted.web import resource
import osaf.contentmodel.photos.Photos as Photos
import traceback
import os, sys, datetime

class PhotosResource(resource.Resource):
    isLeaf = True
    def render_GET(self, request):

        result = []
        output = result.append

        try:

            # The Server item will give us the repositoryView during
            # startup.
            repoView = self.repositoryView

            if not request.postpath or request.postpath[0] == "":
                output("<html><head><title>Photos</title><link rel='stylesheet' href='/site.css' type='text/css' /></head>")
                output("<body>")
                output("<h3>Photos</h3><br>")

                photoList = []
                for photo in Photos.PhotoMixin.iterItems(view=repoView):
                    photoList.append(photo)
                    if not hasattr(photo, 'dateTaken'):
                        photo.dateTaken = datetime.datetime.now()

                photoList.sort(lambda x, y: cmp(y.dateTaken, x.dateTaken))

                for photo in photoList:
                    output("<a href=/photos/%s><img src=/lobster/%s/photoBody height=128 alt='%s'></a>" % (photo.itsUUID, photo.itsUUID, photo.displayName))
                output("</body></html>")

            else:
                uuid = request.postpath[0]
                photo = repoView.findUUID(uuid)
                if photo is None:
                    output("<h3>Photo not found: %s</h3>" % uuid)

                else:
                    output("<html><head><title>%s</title><link rel='stylesheet' href='/site.css' type='text/css' /></head>" % photo.displayName)
                    output("<body>")

                    output("<span class=title>%s</span><br>" % photo.displayName)
                    output("<img src=/lobster/%s/photoBody>" % photo.itsUUID)

        except Exception, e:
            output("<html>Caught an exception: %s<br> %s</html>" % (e, "<br>".join(traceback.format_tb(sys.exc_traceback))))

        return str("\n".join(result))
