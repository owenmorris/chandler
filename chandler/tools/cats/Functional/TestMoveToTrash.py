import tools.cats.framework.ChandlerTestLib as QAUITestAppLib
from tools.cats.framework.ChandlerTestCase import ChandlerTestCase
import osaf.framework.scripting as scripting

from time import strftime, localtime

class TestMoveToTrash(ChandlerTestCase):
    
    def startTest(self):
    
        # creation
        note = QAUITestAppLib.UITestItem("Note", self.logger)
        # actions
        note.SetAttr(displayName="A note to move to Trash", body="TO MOVE TO TRASH")
        note.MoveToTrash()
        # verification
        note.Check_ItemInCollection("Trash")
        note.Check_ItemInCollection("All", expectedResult=False)
        
        today = strftime('%m/%d/%y',localtime())
    
        view = QAUITestAppLib.UITestView(self.logger)
        view.SwitchToCalView()
        view.GoToToday()
    
        sidebar = QAUITestAppLib.App_ns.sidebar
        col = QAUITestAppLib.UITestItem("Collection", self.logger)
        col.SetDisplayName("Trash testing")
        scripting.User.emulate_sidebarClick(sidebar, 'Trash testing')
    
    
        event = QAUITestAppLib.UITestItem("Event", self.logger)
    
        event.SetAttr(startDate=today, startTime="12:00 PM",
                      displayName="Ephemeral event")
        
        event.SelectItem()
        event.Check_ItemInCollection("All", expectedResult=True)
        event.Check_ItemSelected()
        
        event.MoveToTrash()
        
        scripting.User.emulate_sidebarClick(sidebar, 'My calendar')
    
        event.SelectItem(catchException=True)
        event.Check_ItemInCollection("All", expectedResult=False)
        event.Check_ItemSelected(expectedResult=False)
        
