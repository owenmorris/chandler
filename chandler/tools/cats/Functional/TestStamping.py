import tools.cats.framework.ChandlerTestLib as QAUITestAppLib
from tools.cats.framework.ChandlerTestCase import ChandlerTestCase

class TestStamping(ChandlerTestCase):

    def startTest(self):

        note = QAUITestAppLib.UITestItem("Note", self.logger)
        
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
        self.logger.startAction("Remove all stamps")
        note.StampAsCalendarEvent(False, timeInfo=False)
        note.StampAsTask(False, timeInfo=False)
        note.StampAsMailMessage(False, timeInfo=False)
        self.logger.endAction(True)
        
        # verification
        note.Check_DetailView({"stampMail":False,"stampTask":False, "stampEvent":False})


