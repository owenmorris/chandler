
import  wx
import  wx.colheader

#----------------------------------------------------------------------

class TestPanel(wx.Panel):
    def __init__(self, parent, log):
        wx.Panel.__init__(self, parent, -1,
                         style=wx.NO_FULL_REPAINT_ON_RESIZE)
        self.log = log

        l0 = wx.StaticText(self, -1, "(click result)", (10, 150), (150, 20))

        l1 = wx.StaticText(self, -1, "wx.ColumnHeader (1)", (20, 20), (150, 20))

        ch1 = wx.colheader.ColumnHeader(self, 711, (20, 40), (350, 20), 0)
        ch1.AppendItem("Sun", wx.colheader.COLUMNHEADER_JUST_Center, 50, 1, 1)
        ch1.AppendItem("Mon", wx.colheader.COLUMNHEADER_JUST_Center, 50, 0, 1)
        ch1.AppendItem("Tue", wx.colheader.COLUMNHEADER_JUST_Center, 50, 0, 1)
        ch1.AppendItem("Wed", wx.colheader.COLUMNHEADER_JUST_Center, 50, 0, 1)
        ch1.AppendItem("Thu", wx.colheader.COLUMNHEADER_JUST_Center, 50, 0, 1)
        ch1.AppendItem("Fri", wx.colheader.COLUMNHEADER_JUST_Center, 50, 0, 1)
        ch1.AppendItem("Sat", wx.colheader.COLUMNHEADER_JUST_Center, 50, 0, 1)
        ch1.SetToolTipString("Column header (1)")
        self.Bind(wx.EVT_BUTTON, self.OnClick, ch1)

        #tb = ch1.GetLabelText(2)
        #lz = wx.StaticText(self, -1, tb, (100, 20), (120, 20))

        l2 = wx.StaticText(self, -1, "wx.ColumnHeader (2)", (80, 70), (150, 20))

        ch2 = wx.colheader.ColumnHeader(self, 711, (80, 90), (270, 20), 0)
        ch2.AppendItem("Juan", wx.colheader.COLUMNHEADER_JUST_Left, 90, 1, 1)
        ch2.AppendItem("Valdéz", wx.colheader.COLUMNHEADER_JUST_Center, 90, 0, 1)
        ch2.AppendItem("coffeehead", wx.colheader.COLUMNHEADER_JUST_Right, 90, 0, 1)
        ch2.SetToolTipString("Column header (2)")
        self.Bind(wx.EVT_BUTTON, self.OnClick, ch2)

    def OnClick(self, event):
        l0.SetLabelText("clicked!")
        self.log.write("Click! (%d)\n" % event.GetId())


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

