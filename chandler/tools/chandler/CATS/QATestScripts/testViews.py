import osaf.framework.scripting.QATestAppLib as QATestAppLib
import wx
logger = QATestAppLib.Logger()
ApplicationBarAll()

logger.Start("All View to Mail View")
ApplicationBarMail()
wx.GetApp().Yield()
logger.Stop()
mailButton = FindNamedBlock("ApplicationBarMailButton")
if mailButton.widget.IsToggled():
    logger.ReportPass("Checking Mail toolbar button")
else:
    logger.ReportFailure("Checking Mail toolbar button: button not enabled")
logger.SetChecked(True)
logger.Report()

logger.Start("Mail View to Task View")
ApplicationBarTask()
wx.GetApp().Yield()
logger.Stop()
taskButton = FindNamedBlock("ApplicationBarTaskButton")
if taskButton.widget.IsToggled():
    logger.ReportPass("Checking Task toolbar button")
else:
    logger.ReportFailure("Checking Task toolbar button: button not enabled")
logger.SetChecked(True)
logger.Report()

logger.Start("Task View to Calendar View")
ApplicationBarEvent()
wx.GetApp().Yield()
logger.Stop()
eventButton = FindNamedBlock("ApplicationBarEventButton")
if eventButton.widget.IsToggled():
    logger.ReportPass("Checking Calendar toolbar button")
else:
    logger.ReportFailure("Checking Calendar toolbar button: button not enabled")
logger.SetChecked(True)
logger.Report()

logger.Start("Calendar View to All View")
ApplicationBarAll()
wx.GetApp().Yield()
logger.Stop()
allButton = FindNamedBlock("ApplicationBarAllButton")
if allButton.widget.IsToggled():
    logger.ReportPass("Checking All toolbar button")
else:
    logger.ReportFailure("Checking All toolbar button: button not enabled")
logger.SetChecked(True)
logger.Report()
logger.Close()