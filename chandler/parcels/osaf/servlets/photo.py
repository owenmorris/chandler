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


from osaf import webserver
import traceback
import sys, datetime

class PhotosResource(webserver.AuthenticatedResource):
    isLeaf = True
    def render_GET(self, request):

        from photos import PhotoMixin

        result = []
        output = result.append

        try:

            # The Server item will give us the repositoryView during
            # startup.
            repoView = self.myView

            if not request.postpath or request.postpath[0] == "":
                output(u"<html><head><meta http-equiv='Content-Type' content='text/html; charset=utf-8'><title>Photos</title><link rel='stylesheet' href='/site.css' type='text/css' /></head>")
                output(u"<body>")
                output(u"<h3>Photos</h3><br>")

                photoList = []
                for photo in PhotoMixin.iterItems(repoView):
                    photoList.append(photo)
                    if not hasattr(photo, 'dateTaken'):
                        photo.dateTaken = datetime.datetime.now(repoView.tzinfo.default)

                photoList.sort(lambda x, y: cmp(y.dateTaken, x.dateTaken))

                for photo in photoList:
                    output(u"<a href=/photos/%s><img src=/lobs/%s/photoBody height=128 alt='%s'></a>" % (photo.itsUUID, photo.itsUUID, photo.displayName))
                output(u"</body></html>")

            else:
                uuid = request.postpath[0]
                photo = repoView.findUUID(uuid)
                if photo is None:
                    output(u"<h3>Photo not found: %s</h3>" % uuid)

                else:
                    output(u"<html><head><title>%s</title><link rel='stylesheet' href='/site.css' type='text/css' /></head>" % photo.displayName)
                    output(u"<body>")

                    output(u"<span class=title>%s</span><br>" % photo.displayName)
                    output(u"<img src=/lobs/%s/photoBody>" % photo.itsUUID)

        except Exception, e:
            output(u"<html>Caught an exception: %s<br> %s</html>" % (e, "<br>".join(traceback.format_tb(sys.exc_traceback))))


        return "\n".join(result).encode('utf-8', 'replace')
