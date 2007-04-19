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


import logging
from osaf import webserver

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

