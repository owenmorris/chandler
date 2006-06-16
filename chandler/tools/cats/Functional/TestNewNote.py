import tools.cats.framework.ChandlerTestLib as QAUITestAppLib
from tools.cats.framework.ChandlerTestCase import ChandlerTestCase
from i18n.tests import uw
    
class TestNewNote(ChandlerTestCase):
    
    def startTest(self):
        
        note = QAUITestAppLib.UITestItem("Note", self.logger)
        
        # action
        note.SetAttr(displayName=uw("A note to myself about filing taxes"), body=uw("FILE TAXES!"))
        
        # verification
        note.Check_DetailView({"displayName":uw("A note to myself about filing taxes"),"body":uw("FILE TAXES!")})
     
