#   Copyright (c) 2003-2007 Open Source Applications Foundation
#
#   Licensed under the Apache License, Version 2.0 (the "License");
#   you may not use this file except in compliance with the License.
#   You may obtain a copy of the License at
#
#       http://www.apache.org/licenses/LICENSE-2.0
#
#   Unless required by applicable law or agreed to in writing, software
#   distributed under the License is distributed on an "AS IS" BASIS,
#   WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
#   See the License for the specific language governing permissions and
#   limitations under the License.

import  wx
from i18n import ChandlerMessageFactory as _
import Utility

class Printing(object):
    def __init__(self, frame, canvas):
        super (Printing, self).__init__ ()
        self.frame = frame
        self.canvas = canvas
        self.printData = wx.PrintData()
        self.printData.SetPaperId(wx.PAPER_LETTER)
        self.printData.SetPrintMode(wx.PRINT_MODE_PRINTER)
        # default orientation is landscape
        self.printData.SetOrientation(wx.LANDSCAPE)

    def OnPageSetup(self):
        data = wx.PageSetupDialogData(self.printData)
        data.CalculatePaperSizeFromId()
        printerDialog = wx.PageSetupDialog(self.canvas, data)
        printerDialog.ShowModal()
        self.printData = wx.PrintData(printerDialog.GetPageSetupData().GetPrintData())
        printerDialog.Destroy()

    def OnPrintPreview(self):
        data = wx.PrintDialogData(self.printData)
        previewPrintout = CanvasPrintout(self.canvas)
        printingPrintout = CanvasPrintout(self.canvas)
        self.preview = wx.PrintPreview(previewPrintout, printingPrintout, data)
        if wx.Platform == '__WXGTK__':
            self.preview.SetZoom(150)

        if not self.preview.Ok():
            return

        frame = wx.PreviewFrame(self.preview, self.frame, _(u"Print Preview"))

        frame.Initialize()
        frame.SetPosition(self.frame.GetPosition())
        frame.SetSize(self.frame.GetSize())
        frame.Show(True)

    def OnPrint(self):
        data = wx.PrintDialogData(self.printData)
        data.SetToPage(1)
        printer = wx.Printer(data)
        printout = CanvasPrintout(self.canvas)

        printSuccess = printer.Print(self.frame, printout, True)
        if not printSuccess:
            printError = printer.GetLastError()
            if ((printError != wx.PRINTER_CANCELLED) and (printError != 0)):
                wx.MessageBox(_(u"There was a problem printing.\nCheck your printer and try again."),
                              _(u"Printing..."),
                              wx.OK,
                              parent=wx.GetApp().mainFrame)
        else:
            self.printData = wx.PrintData( printer.GetPrintDialogData().GetPrintData() )
        printout.Destroy()


class CanvasPrintout(wx.Printout):
    def __init__(self, canvas):
        wx.Printout.__init__(self)
        self.canvas = canvas

    def GetPageInfo(self):
        return (1, 1, 1, 1)

    def OnPrintPage(self, page):
        dc = self.GetDC()

        try:
            self.canvas.columnCanvas
        except AttributeError:
            canvas = self.canvas
            width, height = self.canvas.GetVirtualSize()
        else:
            canvas = self.canvas.columnCanvas
            width, height = self.canvas.columnCanvas.GetVirtualSize()

        ppiPaper = self.GetPPIPrinter()
        ppiScreen = self.GetPPIScreen()

        # c.f. wxPython In Action, Chapter 17. On Mac OS X 10.5, ppiPaper
        # is being returned as (0, 0) which seems weird, but it turns out that
        # not scaling works in that case.
        if ppiPaper != ppiScreen and not 0 in ppiPaper:
            userScale = tuple(ppiPaper[i]/ppiScreen[i] for i in (0,1))
            dc.SetUserScale(*userScale)
        else:
            userScale = (1.0, 1.0)

        # If we're scaling, we want to set the canvas size to match
        # the dc size, after taking the scale into account.
        dcSize = dc.GetSize()
        canvasSize = tuple(dcSize[i]/userScale[i] for i in (0,1))

        # resize the calendar canvas to the size of the printed page
        oldSize = canvas.GetSize()
        canvas.SetSize(canvasSize)

        # print everything
        canvas.PrintCanvas(dc)
        # restore the calendar canvas' old size
        canvas.SetSize(oldSize)

        return True
