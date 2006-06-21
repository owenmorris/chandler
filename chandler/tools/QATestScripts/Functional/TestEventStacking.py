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

"""
Tests for errors when numerious events try to occupy the same time/ date space
"""
import tools.QAUITestAppLib as QAUITestAppLib
from time import localtime
from time import strftime
from i18n.tests import uw

App_ns = app_ns()
today = strftime('%m/%d/%y',localtime())

#initialization
fileName = "TestEventStacking.log"
logger = QAUITestAppLib.QALogger(fileName, "TestEventStacking")

try:
    #Make sure we are in calendar view
    view = QAUITestAppLib.UITestView(logger)
    view.SwitchToCalView()

    #Create a collection and select it
    collection = QAUITestAppLib.UITestItem("Collection", logger)
    collection.SetDisplayName(uw("stacked"))
    sidebar = App_ns.sidebar
    QAUITestAppLib.scripting.User.emulate_sidebarClick(sidebar, uw("stacked"))

    #make sure we are on current week
    view.GoToToday()

    # creation
    for i in range(10):
        eventName = uw("Stacked Event %d" %i)
        event = QAUITestAppLib.UITestItem("Event", logger)

        #action
        event.SetAttr(displayName=eventName, location=uw("location"),startDate=today, startTime="12:00 PM", body=uw("Stacked event test"))

        #verification
        event.Check_DetailView({"displayName":eventName,"location":uw("location"),"startDate":today,"endDate":today,"startTime":"12:00 PM","body":uw("Stacked event test")})

finally:
    #cleaning
    logger.Close()
