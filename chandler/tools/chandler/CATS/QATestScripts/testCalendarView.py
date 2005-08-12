import wx
import osaf.framework.scripting.QATestAppLib as QATestAppLib
import time

logger = QATestAppLib.Logger()

ApplicationBarEvent()
click = wx.MouseEvent(wx.wxEVT_LEFT_DCLICK)
click.m_x = 100
click.m_y = 25
timedCanvas = FindNamedBlock('TimedEventsCanvas')

logger.Start("Creating Calendar View Event")
timedCanvas.widget.ProcessEvent(click)
wx.GetApp().Yield()
timedCanvas.widget.ProcessEvent(click)
Type("Timed Event")
enter = wx.CommandEvent(wx.wxEVT_COMMAND_ENTER)
wx.Window_FindFocus().OnTextEnter(enter)
wx.GetApp().Yield()
logger.Stop()

logger.SetChecked(True)
timedEvent = FindByName(pim.CalendarEvent, "Timed Event")
if timedEvent:
	logger.ReportPass("Checking anytime event creation")
else:
	logger.ReportFailure("Checking anytime event creation: event not created")
logger.Report()
logger.Close()


