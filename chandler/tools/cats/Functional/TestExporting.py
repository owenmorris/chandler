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
import os, wx, sys
import osaf.pim.calendar.Calendar as Calendar
from osaf import sharing, pim

class TestExporting(ChandlerTestCase):

    def startTest(self):
        
        appView = self.app_ns.itsView
        path = os.path.join(os.getenv('CHANDLERHOME'),"tools/cats/DataFiles")
        filename = 'exportTest.ics'
        fullpath = os.path.join(path, filename)
        if os.path.exists(fullpath):
            os.remove(fullpath)
        
        #Upcast path to unicode since Sharing requires a unicode path
        path = unicode(path, sys.getfilesystemencoding())
        share = sharing.OneTimeFileSystemShare(path, 'exportTest.ics',
            sharing.ICalendarFormat, itsView=appView)
     
        self.logger.startAction("Export Test Calendar")
        collection = pim.ListCollection(itsView=appView)
        for event in Calendar.EventStamp.getCollection(appView):
            collection.add(event)
        share.contents = collection
        try:
            share.put()
            self.logger.report(True, name="share.put()")
        except:
            self.logger.report(False, name="share.put()")    
        self.logger.endAction(True)
        


