#
# ColumnHeader.py
#

import wx
import wx.colheader
import images

#----------------------------------------------------------------------

class TestPanel( wx.Panel ):
    def __init__( self, parent, log ):
        wx.Panel.__init__( self, parent, -1, style=wx.NO_FULL_REPAINT_ON_RESIZE )
        self.log = log

        # NB: should be 17 for Mac; 20 for all other platforms
        # wxColumnHeader can handle it
        colHeight = 20

        # "no" to sort arrows for this list
        cntlID = 1001
        prompt = "ColumnHeader (%d)" %(cntlID)
        l1 = wx.StaticText( self, -1, prompt, (20, 20), (200, 20) )

        ch1 = wx.colheader.ColumnHeader( self, cntlID, (20, 40), (350, colHeight), 0 )
        dow = [ "Sun", "Mon", "Tue", "Wed", "Thu", "Fri", "Sat" ]
        for v in dow:
            ch1.AppendItem( v, wx.colheader.COLUMNHEADER_JUST_Center, 50, 0, 0, 1 )
        ch1.SetSelectedItemIndex( 0 )
        self.ch1 = ch1
        self.Bind( wx.colheader.EVT_COLUMNHEADER_SELCHANGED, self.OnColumnHeaderClick, ch1 )
        #ch1.SetToolTipString( "ColumnHeader (%d)" %(cntlID) )

        # "yes" to sort arrows for this list
        cntlID = 1002
        prompt = "ColumnHeader (%d)" %(cntlID)
        l2 = wx.StaticText( self, -1, prompt, (80, 70), (200, 20) )

        # FIXME: charset - conditionalize the high ASCII value
        ch2 = wx.colheader.ColumnHeader( self, cntlID, (80, 90), (270, colHeight), 0 )
        coffeeNames = [ "Juan", "ValdŽz", "coffee guy" ]
        for i, v in enumerate( coffeeNames ):
            ch2.AppendItem( v, wx.colheader.COLUMNHEADER_JUST_Left + i, 90, 0, 1, 1 )
        ch2.SetSelectedItemIndex( 0 )

       # add demo UI controls
        self.ch2 = ch2
        self.Bind( wx.colheader.EVT_COLUMNHEADER_SELCHANGED, self.OnColumnHeaderClick, ch2 )
        #ch2.SetToolTipString( "ColumnHeader (%d)" %(cntlID) )

        l0 = wx.StaticText( self, -1, "[result]", (10, 150), (150, 20) )
        self.l0 = l0

        btn = wx.Button( self, -1, "Resize", (10, 190) )
        self.Bind( wx.EVT_BUTTON, self.OnTestResizeButton, btn )
        self.stepSize = 0
        self.stepDir = -1

        btn = wx.Button( self, -1, "Add Bitmap Item", (110, 190) )
        self.Bind( wx.EVT_BUTTON, self.OnAddBitmapItemButton, btn )

        btn = wx.Button( self, -1, "Delete Selected Item", (275, 190) )
        self.Bind( wx.EVT_BUTTON, self.OnTestDeleteButton, btn )

    def OnColumnHeaderClick( self, event ):
        ch = event.GetEventObject()
        self.l0.SetLabel( "clicked (%d) - selected (%ld)" %(event.GetId(), ch.GetSelectedItemIndex()) )
        # self.log.write( "Click! (%ld)\n" % event.GetEventType() )

    def OnTestResizeButton(self, event):
        curWidth = self.ch1.GetTotalUIExtent()
        if (self.stepSize == 1):
            self.stepDir = (-1)
        else:
            if (self.stepSize == (-1)):
                self.stepDir = 1
        self.stepSize = self.stepSize + self.stepDir
        self.ch1.DoSetSize( 20, 40, curWidth + 40 * self.stepSize, 20, 0 )

    def OnAddBitmapItemButton( self, event ):
        ch = self.ch2
        itemCount = ch.GetItemCount()
        ch.AppendItem( "", wx.colheader.COLUMNHEADER_JUST_Center, 40, 0, 0, 1 )
        testBmp = images.getTest2Bitmap()
        ch.SetBitmapRef( itemCount, testBmp )
        ch.SetSelectedItemIndex( itemCount )
        ch.ResizeToFit()
        self.l0.SetLabel( "added bitmap item (%d) to (%d)" %(itemCount, ch.GetId()) )

    def OnTestDeleteButton( self, event ):
        ch = self.ch1
        itemIndex = ch.GetSelectedItemIndex()
        if (itemIndex >= 0):
            ch.DeleteItem( itemIndex )
            self.l0.SetLabel( "deleted item (%d) from (%d)" %(itemIndex, ch.GetId()) )
        else:
            self.l0.SetLabel( "header (%d): no item selected" %(ch.GetId()) )

#----------------------------------------------------------------------

def runTest( frame, nb, log ):
    win = TestPanel( nb, log )
    return win

#----------------------------------------------------------------------


overview = """<html><body>
<h2>ColumnHeader</h2>

<p>A ColumnHeader control displays a set of joined, native-appearance button-ish things.</p>

<p>Native column headers can be found in many views, most notably in a folder Details view.</p>

<p>This control embodies the native look and feel to the greatest practical degree, and fills in some holes to boot.</p>

<p>A limitation: text and bitmaps are mutually exclusive.</p>

<p>The MSW version of this control will have a persistant selection indicator. The native MSW control has no canonical selection UI, instead using a sort arrow to serve double-duty as a selection indicator; nonetheless, it has a rollover indicator.</p>

<p>The GTK framework lacks, or appears to lack, a native control: a simple bevel button shall suffice for the theme background.</p>

</body></html>
"""


if __name__ == '__main__':
    import sys,os
    import run
    run.main(['', os.path.basename(sys.argv[0])] + sys.argv[1:])

