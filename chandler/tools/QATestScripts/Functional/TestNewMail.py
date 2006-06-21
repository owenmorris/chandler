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
from i18n.tests import uw

# initialization
fileName = "TestNewMail.log"
logger = QAUITestAppLib.QALogger(fileName, "TestNewMail")

try:
    # creation
    mail = QAUITestAppLib.UITestItem("MailMessage", logger)

    # action
    mail.SetAttr(displayName=uw("Invitation Mail"), toAddress="demo2@osafoundation.org", body=uw("This is an email to invite you"))
    mail.SendMail()

    # verification
    mail.Check_DetailView({"displayName":uw("Invitation Mail"),"toAddress":"demo2@osafoundation.org","body":uw("This is an email to invite you")})
    
finally:
    #cleaning
    logger.Close()
