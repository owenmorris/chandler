import tools.QAUITestAppLib as QAUITestAppLib
from i18n.tests import uw

# initialization
fileName = "TestNewNote.log"
logger = QAUITestAppLib.QALogger(fileName, "TestNewNote")

try:
    # creation
    note = QAUITestAppLib.UITestItem("Note", logger)

    # action
    note.SetAttr(displayName=uw("A note to myself about filing taxes"), body=uw("FILE TAXES!"))

    # verification
    note.Check_DetailView({"displayName":uw("A note to myself about filing taxes"),"body":uw("FILE TAXES!")})
    
finally:
    # cleaning
    logger.Close()
