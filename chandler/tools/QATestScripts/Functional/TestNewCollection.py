import tools.QAUITestAppLib as QAUITestAppLib
    
# initialization
fileName = "TestNewCollection.log"
logger = QAUITestAppLib.QALogger(fileName, "TestNewCollection")

try:
    # action
    col = QAUITestAppLib.UITestItem("Collection", logger)
    # verification
    col.Check_Collectionexistence("Untitled")
    
    # action
    col.SetDisplayName("Meeting")
    # verification
    col.Check_Collectionexistence("Meeting")
    
    # action
    note = QAUITestAppLib.UITestItem("Note", logger)
    note.AddCollection("Meeting")
    # verification
    note.Check_ItemInCollection("Meeting")

finally:
    # cleaning
    logger.Close()
