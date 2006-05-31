import tools.QAUITestAppLib as QAUITestAppLib
import osaf.framework.scripting as scripting
from i18n.tests import uw

# initialization
fileName = "TestDeleteCollection.log"
logger = QAUITestAppLib.QALogger(fileName, "TestDeleteCollection")

try:
    # creation
    col = QAUITestAppLib.UITestItem("Collection", logger)
    col.SetDisplayName(uw("ToBeDeleted"))
    # action
    App_ns = scripting.app_ns()
    sb = App_ns.sidebar
    # move focus from collection name text to collection
    scripting.User.emulate_sidebarClick(sb, uw("ToBeDeleted"))
    col.DeleteCollection()

    # verification
    col.Check_CollectionExistence(expectedResult=False)

    # create it back for the next tests that depend on it (kludge)
    col = QAUITestAppLib.UITestItem("Collection", logger)
finally:
    #cleaning
    logger.Close()
