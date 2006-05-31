import tools.QAUITestAppLib as QAUITestAppLib
from i18n.tests import uw

# initialization
fileName = "TestNewItem.log"
logger = QAUITestAppLib.QALogger(fileName, "TestNewItem")

START_ITEM = QAUITestAppLib.App_ns.DetailRoot.contents

def switchAndCheck(logger, buttonName, expectedClass):

    name = uw("TestNewItem(%s)" % (buttonName,))
    logger.Start(name)

    # Switch to the requested view...
    QAUITestAppLib.App_ns.appbar.press(name=buttonName)
 
    # ... idle() so the app can handle changes
    QAUITestAppLib.scripting.User.idle()

    # ... Create a new item (For some reason, calling
    # scripting.User.emulate_typing() didn't correctly
    # simulate a control/cmd-n here)
    QAUITestAppLib.App_ns.MainView.onNewItemEvent(
       QAUITestAppLib.App_ns.NewItemItem.event)

    # ... wait again so the app can refresh
    QAUITestAppLib.scripting.User.idle()

    # See what's in the detail view
    newItem = QAUITestAppLib.App_ns.DetailRoot.contents

    # Verify we got what we expected
    global START_ITEM
    if newItem is START_ITEM:
        logger.ReportFailure("Selection in detail view didn't change!")
    elif newItem.__class__ != expectedClass:
        logger.ReportFailure("Expected a %s, got %s" % (expectedClass, newItem))
    else:
        logger.ReportPass("Created a %s" % (expectedClass))

    # Random QAUITestAppLib nonsense
    logger.SetChecked(True)
    logger.Report(name)
    logger.Stop()

try:

    switchAndCheck(logger, "ApplicationBarAllButton",
                   QAUITestAppLib.pim.notes.Note)
    
    switchAndCheck(logger, "ApplicationBarEventButton",
                   QAUITestAppLib.pim.calendar.CalendarEvent)
    
    switchAndCheck(logger, "ApplicationBarMailButton",
                   QAUITestAppLib.Mail.MailMessage)
    
    switchAndCheck(logger, "ApplicationBarTaskButton",
                   QAUITestAppLib.pim.Task)

finally:
    # cleanup
    logger.Close()
