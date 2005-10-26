import tools.QAUITestAppLib as QAUITestAppLib

# initialization
fileName = "TestMoveToTrash.log"
logger = QAUITestAppLib.QALogger(fileName, "TestMoveToTrash")

try:
    # creation
    note = QAUITestAppLib.UITestItem("Note", logger)
    # actions
    note.SetAttr(displayName="A note to move to Trash", body="TO MOVE TO TRASH")
    note.MoveToTrash()
    # verification
    note.Check_ItemInCollection("Trash")
    note.Check_ItemInCollection("All", expectedResult=False)
finally:
    # cleaning
    logger.Close()
