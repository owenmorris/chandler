import osaf.framework.scripting.QATestAppLib as QATestAppLib
import wx
logger = QATestAppLib.Logger()
ApplicationBarAll()

logger.Start("All View to Mail View")
ApplicationBarMail()
wx.GetApp().Yield()
logger.Stop()
logger.Report()

logger.Start("Mail View to Task View")
ApplicationBarTask()
wx.GetApp().Yield()
logger.Stop()
logger.Report()

logger.Start("Task View to Calendar View")
ApplicationBarEvent()
wx.GetApp().Yield()
logger.Stop()
logger.Report()

logger.Start("Calendar View to All View")
ApplicationBarAll()
wx.GetApp().Yield()
logger.Stop()
logger.Report()
logger.Close()