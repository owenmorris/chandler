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

import wx
import tools.QAUITestAppLib as QAUITestAppLib

# initialization
fileName = "PerfStampEvent.log"
logger = QAUITestAppLib.QALogger(fileName, "Perf Stamp as Event")

frame = wx.GetApp().mainFrame
frame.SetSize((1024, 720))

try:
    # Test in calendar view
    app_ns().appbar.press("ApplicationBarEventButton")
    wx.GetApp().Yield(True)
    QAUITestAppLib.UITestItem("Collection")

    # creation
    note = QAUITestAppLib.UITestItem("Note", logger)

    # action
    note.StampAsCalendarEvent(True)
    
    # verification
    note.Check_DetailView({"stampEvent":True})

finally:
    # cleaning
    logger.Close()
