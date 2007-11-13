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
    'CalDAVRecordSetConduit',
]

import PyICU
import webdav_conduit
from i18n import ChandlerMessageFactory as _
from osaf.pim.calendar.TimeZone import serializeTimeZone
import time

import logging

logger = logging.getLogger(__name__)



class CalDAVRecordSetConduit(webdav_conduit.WebDAVRecordSetConduit):


    def _createCollectionResource(self, handle, resource, childName):
        displayName = self.share.contents.displayName
        timezone = serializeTimeZone(PyICU.ICUtzinfo.default)
        return handle.blockUntil(resource.createCalendar, childName,
                                 displayName, timezone)

    def getCollectionName(self):
        container = self._getContainerResource()
        try:
            result = container.serverHandle.blockUntil(container.getDisplayName)
        except:
            result = _(u"Unknown")

        return result

    def getPath(self, uuid):
        return "%s.ics" % uuid


    def putResource(self, text, path, etag=None, debug=False):
        resource = self._resourceFromPath(path)
        start = time.time()
        self._getServerHandle().blockUntil(resource.put, text,
            checkETag=False, contentType="text/calendar")
        end = time.time()
        self.networkTime += (end - start)
        return resource.etag.strip('"') # .mac puts quotes around the etag

