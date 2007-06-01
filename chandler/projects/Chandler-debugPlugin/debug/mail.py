#   Copyright (c) 2007 Open Source Applications Foundation
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

import pkg_resources

from application import schema
from osaf.pim import SmartCollection
from osaf.mail.message import messageTextToKind


def loadMailTests(view, datadir):
    try:
        sidebar = schema.ns('osaf.app', view).sidebarCollection

        for col in sidebar:
            if datadir == col.displayName:
                #We already imported these mail messages
                return

        files = pkg_resources.resource_listdir('debug', datadir)
        mCollection = SmartCollection(itsView=view)
        mCollection.displayName = unicode(datadir)

        for f in files:
            if not f.startswith('test_'):
                continue

            fp = pkg_resources.resource_stream('debug', "%s/%s" %(datadir, f))
            messageText = fp.read()
            fp.close()

            mailStamp = messageTextToKind(view, messageText)
            mCollection.add(mailStamp.itsItem)

        sidebar.add(mCollection)

    except:
        view.cancel()
        raise
