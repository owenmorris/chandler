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

import tools.cats.framework.ChandlerTestLib as QAUITestAppLib
from tools.cats.framework.ChandlerTestCase import ChandlerTestCase
import os, wx, sys
import osaf.pim.calendar.Calendar as Calendar
from osaf import sharing, pim
import application.Globals as Globals

class TestExporting(ChandlerTestCase):

    def startTest(self):
        
        appView = self.app_ns.itsView
        path = os.path.join(Globals.chandlerDirectory,"tools/cats/DataFiles")
        filename = 'exportTest.ics'
        fullpath = os.path.join(path, filename)
        if os.path.exists(fullpath):
            os.remove(fullpath)
        
        #Upcast path to unicode since Sharing requires a unicode path
        fullpath = unicode(fullpath, sys.getfilesystemencoding())
        self.logger.startAction("Export Test Calendar")
        collection = pim.ListCollection(itsView=appView)
        for event in Calendar.EventStamp.getCollection(appView):
            collection.add(event)
        try:
            sharing.exportFile(appView, fullpath, collection)
            self.logger.report(True, name="exportFile")
        except:
            self.logger.report(False, name="exportFile")    
        self.logger.endAction(True)
        


