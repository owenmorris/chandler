import tools.cats.framework.ChandlerTestLib as QAUITestAppLib
from tools.cats.framework.ChandlerTestCase import ChandlerTestCase
    
class TestNewNote(ChandlerTestCase):
    
    def startTest(self):
        
        note = QAUITestAppLib.UITestItem("Note", self.logger)
        
        # action
        note.SetAttr(displayName="A note to myself about filing taxes", body="FILE TAXES!")
        
        # verification
        note.Check_DetailView({"displayName":"A note to myself about filing taxes","body":"FILE TAXES!"})
        
