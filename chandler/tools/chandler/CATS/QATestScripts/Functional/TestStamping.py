import osaf.framework.QAUITestAppLib as QAUITestAppLib
import os

filePath = os.path.expandvars('$CATSREPORTDIR')
if not os.path.exists(filePath):
    filePath = os.getcwd()

#initialization
fileName = "TestStamping.log"
logger = QAUITestAppLib.QALogger(os.path.join(filePath, fileName),"TestStamping")
note = QAUITestAppLib.UITestItem("Note", logger)

#action
#stamp as a mail
note.logger.Start("Stamp as a mail message")
note.StampAsMailMessage(True)
note.logger.Stop()
#verification
note.Check_DetailView({"stampMail":True,"stampTask":False, "stampEvent":False})
#stamp as a task
note.logger.Start("Stamp as a task")
note.StampAsTask(True)
note.logger.Stop()
#stamp as an event
note.logger.Start("Stamp as an event")
note.StampAsCalendarEvent(True)
note.logger.Stop()
#verification
note.Check_DetailView({"stampMail":True,"stampTask":True, "stampEvent":True})
#remove all stamp
note.logger.Start("remove all stamp")
note.StampAsCalendarEvent(False)
note.StampAsTask(False)
note.StampAsMailMessage(False)
note.logger.Stop()
#verification
note.Check_DetailView({"stampMail":False,"stampTask":False, "stampEvent":False})

#cleaning
logger.Close()
