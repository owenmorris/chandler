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
import osaf.framework.scripting as scripting
from i18n.tests import uw

class TestDeleteCollection(ChandlerTestCase):
    
    def startTest(self):
        
        #make sure we start in the calendar view
        QAUITestAppLib.UITestItem("Collection", self.logger)
        QAUITestAppLib.UITestView(self.logger).SwitchToCalView()
        
        # creation
        col = QAUITestAppLib.UITestItem("Collection", self.logger)
        col.SetDisplayName(uw("ToBeDeleted"))
    
        # action
        sb = self.app_ns.sidebar
        # move focus from collection name text to collection. This
        # requires 2 clicks
        scripting.User.emulate_sidebarClick(sb, uw("ToBeDeleted"))
        scripting.User.emulate_sidebarClick(sb, uw("ToBeDeleted"))
        col.DeleteCollection()
    
        # verification
        col.Check_CollectionExistence(expectedResult=False)
    

