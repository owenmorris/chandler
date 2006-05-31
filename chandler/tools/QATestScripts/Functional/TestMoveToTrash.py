import tools.QAUITestAppLib as QAUITestAppLib
import osaf.framework.scripting as scripting

from time import strftime, localtime
from i18n.tests import uw

# initialization
fileName = "TestMoveToTrash.log"
logger = QAUITestAppLib.QALogger(fileName, "TestMoveToTrash")

try:
    # creation
    note = QAUITestAppLib.UITestItem("Note", logger)
    # actions
    note.SetAttr(displayName=uw("A note to move to Trash"), body=uw("TO MOVE TO TRASH"))
    note.MoveToTrash()
    # verification
    note.Check_ItemInCollection("Trash")
    note.Check_ItemInCollection("All", expectedResult=False)
    
    today = strftime('%m/%d/%y',localtime())

    view = QAUITestAppLib.UITestView(logger)
    view.SwitchToCalView()
    view.GoToToday()

    sidebar = QAUITestAppLib.App_ns.sidebar
    col = QAUITestAppLib.UITestItem("Collection", logger)
    col.SetDisplayName(uw("Trash testing"))
    scripting.User.emulate_sidebarClick(sidebar, uw('Trash testing'))


    event = QAUITestAppLib.UITestItem("Event", logger)

    event.SetAttr(startDate=today, startTime="12:00 PM",
                  displayName=uw("Ephemeral event"))

    event.SelectItem()
    event.Check_ItemInCollection("All", expectedResult=True)
    event.Check_ItemSelected()

    event.MoveToTrash()

    scripting.User.emulate_sidebarClick(sidebar, "My calendar")

    event.SelectItem(catchException=True)
    event.Check_ItemInCollection("All", expectedResult=False)
    event.Check_ItemSelected(expectedResult=False)

finally:
    # cleaning
    logger.Close()
