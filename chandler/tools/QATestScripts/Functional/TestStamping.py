import tools.QAUITestAppLib as QAUITestAppLib

#initialization
fileName = "TestStamping.log"
logger = QAUITestAppLib.QALogger(fileName, "TestStamping")

try:
    # creation
    note = QAUITestAppLib.UITestItem("Note", logger)
    
    # action
    # stamp as a mail
    note.StampAsMailMessage(True)
    # verification
    note.Check_DetailView({"stampMail":True,"stampTask":False, "stampEvent":False})
    # stamp as a task
    note.StampAsTask(True)
    # stamp as an event
    note.StampAsCalendarEvent(True)
    # verification
    note.Check_DetailView({"stampMail":True,"stampTask":True, "stampEvent":True})
    # remove all stamps
    note.logger.Start("Remove all stamps")
    note.StampAsCalendarEvent(False, timeInfo=False)
    note.StampAsTask(False, timeInfo=False)
    note.StampAsMailMessage(False, timeInfo=False)
    note.logger.Stop()
    
    # verification
    note.Check_DetailView({"stampMail":False,"stampTask":False, "stampEvent":False})

finally:
    # cleaning
    logger.Close()
