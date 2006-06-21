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
fileName = "TestDeleteCollection.log"
logger = QAUITestAppLib.QALogger(fileName, "TestDeleteCollection")

try:
    # creation
    col = QAUITestAppLib.UITestItem("Collection", logger)
    col.SetDisplayName(uw("ToBeDeleted"))
    # action
    App_ns = scripting.app_ns()
    sb = App_ns.sidebar
    # move focus from collection name text to collection
    scripting.User.emulate_sidebarClick(sb, uw("ToBeDeleted"))
    col.DeleteCollection()

    # verification
    col.Check_CollectionExistence(expectedResult=False)

    # create it back for the next tests that depend on it (kludge)
    col = QAUITestAppLib.UITestItem("Collection", logger)
finally:
    #cleaning
    logger.Close()
