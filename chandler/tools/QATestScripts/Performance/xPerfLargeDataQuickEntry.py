#   Copyright (c) 2003-2008 Open Source Applications Foundation
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
from osaf.framework.blocks.Block import Block
from osaf.framework.scripting import User
from application import schema

# Test Phase: Initialization
logger = QAUITestAppLib.QALogger("PerfLargeDataQuickEntry.log",
                                 "QuickEntry")

try:
    testView = QAUITestAppLib.UITestView(logger)

    block = Block.findBlockByName("ApplicationBarQuickEntry")
    quickEntryWidget = block.widget
    quickEntryWidget.SetFocus()

    User.emulate_typing("Dinner at 7 pm tomorrow night")

    # XXX I'd really just like to be able to call User.emulate_return() in the
    # XXX timed part below, but for some reason it does not work.
    keyEvent = wx.KeyEvent()
    keyEvent.m_keyCode = wx.WXK_RETURN
    keyEvent.arguments = {'sender': block}
    mainView = schema.ns("osaf.views.main",
                         wx.GetApp().UIRepositoryView).MainView

    # Time how long it takes to create the event starting from pressing ENTER
    logger.Start("Quick entry")
    mainView.onQuickEntryEvent(keyEvent) # XXX See above
    User.idle()
    logger.Stop()

    # Test Phase: Verification  
    # XXX TODO
    
    logger.SetChecked(True)
    logger.Report("Quick entry")

finally:
    # cleanup
    logger.Close()
