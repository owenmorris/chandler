
from twisted.web import resource
import traceback
import os, sys

class PhotosResource(resource.Resource):
    isLeaf = True
    def render_GET(self, request):
        try: # outer try to handle exceptions

            try: # inner try to restore repository view

                # The Server item will give us the repositoryView during
                # startup.  Set it to be the current view and restore the
                # previous view when we're done.
                repoView = self.repositoryView
                prevView = repoView.setCurrentView()

                photoParcel = repoView.findPath("//parcels/osaf/framework/webserver/servlets/photos")

                if not request.postpath or request.postpath[0] == "":
                    result = "<html><head><title>Photos</title><link rel='stylesheet' href='/site.css' type='text/css' /></head>"
                    result += "<body>"
                    result += "<h3>Photos</h3><br>"
                    photos = photoParcel.findPath("data")
                    for photo in photos.iterChildren():
                        result += "&nbsp;&nbsp;&nbsp;<a href=/photos/%s>%s</a><br>" % (photo.itsName, photo.caption)
                    result += "</body></html>"
                    return str(result)

                name = request.postpath[0]
                photo = photoParcel.findPath("data/%s" % name)
                if photo is None:
                    result += "<h3>Photo not found: %s</h3>" % name
                    return str(result)

                templates = os.path.join(os.path.dirname(photoParcel.file),
                 "templates")
                header = file(os.path.join(templates, "head.html"), "r")
                result = "\n".join(header.readlines())
                header.close()

                result += "<span class=title>%s</span><br>" % photo.caption
                result += "<img src=/photomedia/%s>" % photo.file
                footer = file(os.path.join(templates, "foot.html"), "r")
                result += "\n".join(footer.readlines())
                footer.close()
            finally:
                prevView.setCurrentView()

        except Exception, e:
            result = "<html>Caught an exception: %s<br> %s</html>" % (e, "<br>".join(traceback.format_tb(sys.exc_traceback)))

        return str(result)
