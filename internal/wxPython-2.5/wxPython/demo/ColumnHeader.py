
import  wx
import  wx.colheader

#----------------------------------------------------------------------

class TestPanel( wx.Panel ):
    def __init__( self, parent, log ):
        wx.Panel.__init__( self, parent, -1, style=wx.NO_FULL_REPAINT_ON_RESIZE )
        self.log = log

        l1 = wx.StaticText( self, -1, "wx.ColumnHeader (1001)", (20, 20), (200, 20) )

        ch1 = wx.colheader.ColumnHeader( self, 1001, (20, 40), (350, 20), 0 )
        ch1.AppendItem("Sun", wx.colheader.COLUMNHEADER_JUST_Center, 50, 1, 0, 1)
        ch1.AppendItem("Mon", wx.colheader.COLUMNHEADER_JUST_Center, 50, 0, 0, 1)
        ch1.AppendItem("Tue", wx.colheader.COLUMNHEADER_JUST_Center, 50, 0, 0, 1)
        ch1.AppendItem("Wed", wx.colheader.COLUMNHEADER_JUST_Center, 50, 0, 0, 1)
        ch1.AppendItem("Thu", wx.colheader.COLUMNHEADER_JUST_Center, 50, 0, 0, 1)
        ch1.AppendItem("Fri", wx.colheader.COLUMNHEADER_JUST_Center, 50, 0, 0, 1)
        ch1.AppendItem("Sat", wx.colheader.COLUMNHEADER_JUST_Center, 50, 0, 0, 1)
        self.Bind( wx.colheader.EVT_COLUMNHEADER_SELCHANGED, self.OnColumnHeaderClick, ch1 )
        #ch1.SetToolTipString( "Column header (1)" )
        self.ch1 = ch1

        l2 = wx.StaticText( self, -1, "wx.ColumnHeader (1002)", (80, 70), (200, 20) )

        ch2 = wx.colheader.ColumnHeader( self, 1002, (80, 90), (270, 20), 0 )
        ch2.AppendItem( "Juan", wx.colheader.COLUMNHEADER_JUST_Left, 90, 1, 1, 1 )
        ch2.AppendItem( "Valdéz", wx.colheader.COLUMNHEADER_JUST_Center, 90, 0, 1, 1 )
        ch2.AppendItem( "coffeehead", wx.colheader.COLUMNHEADER_JUST_Right, 90, 0, 1, 1 )
        self.Bind( wx.colheader.EVT_COLUMNHEADER_SELCHANGED, self.OnColumnHeaderClick, ch2 )
        #ch2.SetToolTipString("Column header (2)")
        self.ch2 = ch2

        l0 = wx.StaticText( self, -1, "(click result)", (10, 150), (150, 20) )
        self.l0 = l0

        btn = wx.Button( self, -1, "Resize", (10, 190) )
        self.Bind( wx.EVT_BUTTON, self.OnTestResizeButton, btn )
        self.stepSize = 0
        self.stepDir = 1

    def OnColumnHeaderClick( self, event ):
        ch = event.GetEventObject()
        self.l0.SetLabel( "clicked (%d) - selected (%ld)" %(event.GetId(), ch.GetSelectedItemIndex()) )
        # self.log.write( "Click! (%ld)\n" % event.GetEventType())

    def OnTestResizeButton(self, event):
        if (self.stepSize == 1):
            self.stepDir = (-1)
        else:
            if (self.stepSize == (-1)):
                self.stepDir = 1
        self.stepSize = self.stepSize + self.stepDir
        self.ch1.DoSetSize( 20, 40, 351 + 40 * self.stepSize, 20, 0 )

#----------------------------------------------------------------------

def runTest(frame, nb, log):
    win = TestPanel(nb, log)
    return win

#----------------------------------------------------------------------


overview = """<html><body>
<h2>ColumnHeader</h2>

<p>A ColumnHeader control displays a set of joined, native-appearance button-ish things.</p>

<p>Column headers are just...that!</p>

<p>A nod is as good as a wink to a blind horse.</p>

</body></html>
"""



if __name__ == '__main__':
    import sys,os
    import run
    run.main(['', os.path.basename(sys.argv[0])] + sys.argv[1:])

