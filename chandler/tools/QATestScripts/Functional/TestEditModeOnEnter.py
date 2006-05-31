"""
test that hitting enter key when a collection name or grid row is selected causes text to become editable
"""

import tools.QAUITestAppLib as QAUITestAppLib
import osaf.framework.scripting as scripting
from i18n.tests import uw

# initialization
fileName = "TestEditModeOnEnter.log"
logger = QAUITestAppLib.QALogger(fileName, "TestEditModeOnEnter")

try:
    # test edit on enter for collection names
    # creation
    testCollection = QAUITestAppLib.UITestItem("Collection", logger)

    # action 1 test collection name
    # use enter to shift to edit mode
    testCollection.SelectItem()
    QAUITestAppLib.scripting.User.emulate_return()

    QAUITestAppLib.scripting.User.emulate_typing(uw("NoLongerUntitled"))
    # use enter to leave edit mode
    #except it doesn't work, focus somewhere else for the time being
    #QAUITestAppLib.scripting.User.emulate_return()
    testCollection.FocusInDetailView()

    #verification 1
    testCollection.Check_CollectionExistence(uw("NoLongerUntitled"))

    # switch to summary view
    QAUITestAppLib.UITestView(logger).SwitchToAllView()

    # test edit on enter for summary view rows
    # creation 2
    testEvent = QAUITestAppLib.UITestItem("Event", logger)

    # action 2 
    testEvent.SelectItem()
    QAUITestAppLib.scripting.User.emulate_return()
    #QAUITestAppLib.scripting.User.emulate_return() #until bug 5744 resolved 2 returns needed
    QAUITestAppLib.scripting.User.emulate_typing(uw("Your title here"))
    #QAUITestAppLib.scripting.User.emulate_return()#emulate_return doesn't work here either at svn r9900
    testCollection.FocusInDetailView()

    # verification 2
    # check the detail view of the created event
    testEvent.Check_DetailView({"displayName": uw("Your title here")})

finally:
    # cleaning
    logger.Close()
