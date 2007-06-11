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

import tools.cats.framework.ChandlerTestLib as QAUITestAppLib
from tools.cats.framework.ChandlerTestCase import ChandlerTestCase
import os, sys
from osaf import sharing, pim
import application.Globals as Globals


class TestImporting(ChandlerTestCase):
    
    def startTest(self):
        
        def VerifyEventCreation(title):
            self.logger.startAction("Verify events imported")
            testEvent = self.app_ns.item_named(pim.EventStamp, title)
            if testEvent is not None:
                self.logger.endAction(True, "Testing event creation: '%s'" % title)
            else:
                self.logger.endAction(False, "Testing event creation: '%s' not created" % title)
        
            
        path = os.path.join(Globals.chandlerDirectory, "tools/cats/DataFiles",
            "importTest.ics")
        # Upcast path to unicode since Sharing requires a unicode path
        path = unicode(path, sys.getfilesystemencoding())
        
        self.logger.startAction("Import Large Calendar")
        collection = sharing.importFile(self.app_ns.itsView, path)
        self.app_ns.sidebarCollection.add(collection)
        self.scripting.User.idle()
        self.logger.endAction(True, "Imported calendar")
            
        VerifyEventCreation("Go to the beach")
        VerifyEventCreation("Basketball game")
        VerifyEventCreation("Visit friend")
        VerifyEventCreation("Library")
    
        


    
