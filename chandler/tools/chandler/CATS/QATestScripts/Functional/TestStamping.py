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
note.StampAsMailMessage(True)
#verification
note.Check_DetailView({"stampMail":True,"stampTask":False, "stampEvent":False})
#stamp as a task
note.StampAsTask(True)
#stamp as an event
note.StampAsCalendarEvent(True)
#verification
note.Check_DetailView({"stampMail":True,"stampTask":True, "stampEvent":True})
#remove all stamp
note.logger.Start("Remove all stamps")
note.StampAsCalendarEvent(False, timeInfo=False)
note.StampAsTask(False, timeInfo=False)
note.StampAsMailMessage(False, timeInfo=False)
note.logger.Stop()

#verification
note.Check_DetailView({"stampMail":False,"stampTask":False, "stampEvent":False})

#cleaning
logger.Close()
