import logging
from osaf import webserver
from twisted.web import resource

logger = logging.getLogger(__name__)

class LobViewerResource(webserver.AuthenticatedResource):
    isLeaf = True
    def render_GET(self, request):

        try:
            # The Server item will give us the repositoryView during
            # startup.
            repoView = self.myView

            (uuid, attrName) = request.postpath
            item = repoView.findUUID(uuid)
            attr = getattr(item, attrName)
            mimeType = attr.mimetype
            request.setHeader('Content-Type', mimeType)
            input = attr.getInputStream()
            data = input.read()
            input.close()
            request.setHeader('Content-Length', len(data))
            return data

        except Exception, e:
            logging.exception(e)
            return ""

