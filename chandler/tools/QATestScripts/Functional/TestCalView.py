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

import tools.QAUITestAppLib as QAUITestAppLib
import osaf.framework.scripting as scripting
from i18n.tests import uw
    
# initialization
fileName = "TestCalView.log"
logger = QAUITestAppLib.QALogger(fileName, "TestCalView")

try:
    # creation
    testView = QAUITestAppLib.UITestView(logger)
    # action
    # switch to calendar view
    testView.SwitchToCalView()
    # double click in the calendar view => event creation or selection
    ev = testView.DoubleClickInCalView()
    scripting.User.idle()
    # double click one more time => edit the title
    #testView.DoubleClickInCalView()
    # type a new title and return
    QAUITestAppLib.scripting.User.emulate_typing(uw("Writing tests"))
    QAUITestAppLib.scripting.User.emulate_return()
    
    # verification
    # check the detail view of the created event
    ev.Check_DetailView({"displayName": uw("Writing tests")})

finally:
    # cleaning
    logger.Close()
