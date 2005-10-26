import tools.QAUITestAppLib as QAUITestAppLib
    
# initialization
fileName = "TestNewNote.log"
logger = QAUITestAppLib.QALogger(fileName, "TestNewNote")

try:
    # creation
    note = QAUITestAppLib.UITestItem("Note", logger)
    
    # action
    note.SetAttr(displayName="A note to myself about filing taxes", body="FILE TAXES!")
    
    # verification
    note.Check_DetailView({"displayName":"A note to myself about filing taxes","body":"FILE TAXES!"})
    
finally:
    # cleaning
    logger.Close()
