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

ID_Setup    =   wx.NewId()
ID_Preview  =   wx.NewId()
ID_Print    =   wx.NewId()

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
        
        frame = wx.PreviewFrame(self.preview, self.frame, _(u"Print preview"))
        
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
                wx.MessageBox(_(u"There was a problem printing.\nPerhaps your current printer is not set correctly?"),
                              _(u"Printing"),
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
            width, height = self.canvas.GetVirtualSize()
        else:
            width, height = self.canvas.columnCanvas.GetVirtualSize()
            
        maxX = width
        maxY = height


        # Let's have at least 50 device units margin
        marginX = 50
        marginY = 50

        # Add the margin to the graphic size
        maxX = maxX + (2 * marginX)
        maxY = maxY + (2 * marginY)

        # Get the size of the DC in pixels
        (w, h) = dc.GetSizeTuple()

        # Calculate a suitable scaling factor
        scaleX = float(w) / maxX
        scaleY = float(h) / maxY

        # Use x or y scaling factor, whichever fits on the DC
        actualScale = min(scaleX, scaleY)

        # Calculate the position on the DC for centering the graphic
        posX = (w - (width * actualScale)) / 2.0
        posY = (h - (height * actualScale)) / 2.0

        # Set the scale and origin
        dc.SetUserScale(actualScale, actualScale)
        dc.SetDeviceOrigin(int(posX), int(posY))

        #-------------------------------------------

        self.canvas.PrintCanvas(dc)

        return True

