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

logger = QAUITestAppLib.QALogger("TestCleanRepo.log","TestCleanRepo")

# Make sure the repository isn't corrupted. This will happen automatically
# when Chandler quits, but that happens after we've shut down the testing
# / logging infrastructure. By doing this here, we'll see corruption while
# everything's still set up.
try:
    logger.Start('TestCleanRepo')
    logger.SetChecked(True)
    QAUITestAppLib.App_ns.itsView.check()
    logger.ReportPass('CleanRepo')
    logger.Stop()
finally:
    if len(logger.passedList) < 1:
        logger.ReportFailure('TestCleanRepo')
    logger.Report('TestCleanRepo')
    logger.Close()
