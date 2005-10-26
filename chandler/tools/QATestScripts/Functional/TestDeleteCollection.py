import tools.QAUITestAppLib as QAUITestAppLib

# initialization
fileName = "TestDeleteCollection.log"
logger = QAUITestAppLib.QALogger(fileName, "TestDeleteCollection")

try:
    # creation
    col = QAUITestAppLib.UITestItem("Collection", logger)

    # action
    col.DeleteCollection()

    # verification
    col.Check_CollectionExistance(expectedResult=False)

finally:
    #cleaning
    logger.Close()
