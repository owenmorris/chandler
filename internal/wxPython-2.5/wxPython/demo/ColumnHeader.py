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

        # init (non-UI) demo vars
        # NB: should be 17 for Mac; 20 for all other platforms
        # wxColumnHeader can handle it
        self.baseWidth = 350
        self.colHeight = 20
        self.colStartX = 175
        self.colStartY = 20

        self.stepSize = 0
        self.stepDir = -1

        # "no" to sort arrows for this list
        cntlID = 1001
        prompt = "ColumnHeader (%d)" %(cntlID)
        l1 = wx.StaticText( self, -1, prompt, (self.colStartX, self.colStartY), (200, 20) )

        ch1 = wx.colheader.ColumnHeader( self, cntlID, (self.colStartX, self.colStartY + 20), (self.baseWidth, self.colHeight), 0 )
        dow = [ "Sun", "Mon", "Tue", "Wed", "Thu", "Fri", "Sat" ]
        for v in dow:
            ch1.AppendItem( v, wx.colheader.COLUMNHEADER_JUST_Center, 50, 0, 0, 1 )
        ch1.SetSelectedItem( 0 )
        self.ch1 = ch1
        self.Bind( wx.colheader.EVT_COLUMNHEADER_SELCHANGED, self.OnColumnHeaderClick, ch1 )
        #ch1.SetToolTipString( "ColumnHeader (%d)" %(cntlID) )

        # "yes" to sort arrows for this list
        cntlID = 1002
        prompt = "ColumnHeader (%d)" %(cntlID)
        l2 = wx.StaticText( self, -1, prompt, (self.colStartX, self.colStartY + 80), (200, 20) )

        # FIXME: charset - conditionalize the high ASCII value
        ch2 = wx.colheader.ColumnHeader( self, cntlID, (self.colStartX, self.colStartY + 100), (270, self.colHeight), 0 )
        coffeeNames = [ "Juan", "Valdez", "coffee guy" ]
        for i, v in enumerate( coffeeNames ):
            ch2.AppendItem( v, wx.colheader.COLUMNHEADER_JUST_Left + i, 90, 0, 1, 1 )
        ch2.SetSelectedItem( 0 )

        self.ch2 = ch2
        self.Bind( wx.colheader.EVT_COLUMNHEADER_SELCHANGED, self.OnColumnHeaderClick, ch2 )
        #ch2.SetToolTipString( "ColumnHeader (%d)" %(cntlID) )

        # add demo UI controls
        miscControlsY = 175
        l0O = wx.StaticText( self, -1, "Last Action", (10, miscControlsY), (150, 20) )
        l0 = wx.StaticText( self, -1, "[result]", (10, miscControlsY + 20), (150, 20) )
        self.l0 = l0

        prompt = "[Unicode build: %d]" %(ch1.GetFlagUnicode())
        hasUnicode = ch1.GetFlagUnicode()
        l1 = wx.StaticText( self, -1, prompt, (10, miscControlsY + 60), (150, 20) )

        btn = wx.Button( self, -1, "Resize Bounds", (10, self.colStartY) )
        self.Bind( wx.EVT_BUTTON, self.OnTestResizeBoundsButton, btn )

        btn = wx.Button( self, -1, "Delete Selection", (10, self.colStartY + 25) )
        self.Bind( wx.EVT_BUTTON, self.OnTestDeleteItemButton, btn )

        btn = wx.Button( self, -1, "Add Bitmap Item", (10, self.colStartY + 80 + 10) )
        self.Bind( wx.EVT_BUTTON, self.OnTestAddBitmapItemButton, btn )

        btn = wx.Button( self, -1, "Resize Division", (10, self.colStartY + 80 + 10 + 25) )
        self.Bind( wx.EVT_BUTTON, self.OnTestResizeDivisionButton, btn )

        self.colStartX += 60

        cb1 = wx.CheckBox( self, -1, "Enable", (self.colStartX, miscControlsY), (100, 20), wx.NO_BORDER )
        self.Bind( wx.EVT_CHECKBOX, self.OnTestEnableCheckBox, cb1 )
        cb1.SetValue( True )

        cb2 = wx.CheckBox( self, -1, "Visible Selection", (self.colStartX, miscControlsY + 25), (150, 20), wx.NO_BORDER )
        self.Bind( wx.EVT_CHECKBOX, self.OnTestVisibleSelectionCheckBox, cb2 )
        cb2.SetValue( True )

        cb3 = wx.CheckBox( self, -1, "Proportional Resizing", (self.colStartX, miscControlsY + 50), (200, 20), wx.NO_BORDER )
        self.Bind( wx.EVT_CHECKBOX, self.OnTestProportionalResizingCheckBox, cb3 )
        cb3.SetValue( True )

        self.colStartX -= 60

    def OnColumnHeaderClick( self, event ):
        ch = event.GetEventObject()
        self.l0.SetLabel( "(%d): clicked - selected (%ld)" %(event.GetId(), ch.GetSelectedItem()) )
        # self.log.write( "Click! (%ld)\n" % event.GetEventType() )

    def OnTestResizeBoundsButton( self, event ):
        ch = self.ch1
        if (self.stepSize == 1):
            self.stepDir = (-1)
        else:
            if (self.stepSize == (-1)):
                self.stepDir = 1
        self.stepSize = self.stepSize + self.stepDir
        newSize = self.baseWidth + 40 * self.stepSize
        ch.DoSetSize( self.colStartX, self.colStartY + 20, newSize, 20, 0 )
        self.l0.SetLabel( "(%d): resized bounds to %d" %(ch.GetId(), newSize) )

    def OnTestDeleteItemButton( self, event ):
        ch = self.ch1
        itemIndex = ch.GetSelectedItem()
        if (itemIndex >= 0):
            ch.DeleteItem( itemIndex )
            self.l0.SetLabel( "(%d): deleted item (%d)" %(ch.GetId(), itemIndex) )
        else:
            self.l0.SetLabel( "(%d): no item selected" %(ch.GetId()) )

    def OnTestAddBitmapItemButton( self, event ):
        ch = self.ch2
        itemCount = ch.GetItemCount()
        if itemCount <= 8:
             ch.AppendItem( "", wx.colheader.COLUMNHEADER_JUST_Center, 40, 0, 0, 1 )
             testBmp = images.getTest2Bitmap()
             ch.SetBitmapRef( itemCount, testBmp )
             ch.SetSelectedItem( itemCount )
             ch.ResizeToFit()
             self.l0.SetLabel( "(%d): added bitmap item (%d)" %(ch.GetId(), itemCount) )
        else:
             self.l0.SetLabel( "(%d): enough items!" %(ch.GetId()) )

    def OnTestResizeDivisionButton( self, event ):
        ch = self.ch2
        itemIndex = ch.GetSelectedItem()
        if ((itemIndex > 0) and (itemIndex < ch.GetItemCount())):
            curExtent = ch.GetUIExtent( itemIndex )
            ch.ResizeDivision( itemIndex, curExtent.x - 5 )
            self.l0.SetLabel( "(%d): resized btw. %d and %d" %(ch.GetId(), itemIndex - 1, itemIndex) )
        else:
            self.l0.SetLabel( "(%d): no item selected" %(ch.GetId()) )

    def OnTestEnableCheckBox( self, event ):
        curEnabled = self.ch1.IsEnabled()
        curEnabled = not curEnabled
        self.ch1.Enable( curEnabled )
        self.ch2.Enable( curEnabled )
        self.l0.SetLabel( "enabled (%d)" %(curEnabled) )

    def OnTestVisibleSelectionCheckBox( self, event ):
        curEnabled = self.ch1.GetFlagVisibleSelection()
        curEnabled = not curEnabled
        self.ch1.SetFlagVisibleSelection( curEnabled )
        self.ch2.SetFlagVisibleSelection( curEnabled )
        self.l0.SetLabel( "selection visible (%d)" %(curEnabled) )

    def OnTestProportionalResizingCheckBox( self, event ):
        curEnabled = self.ch1.GetFlagProportionalResizing()
        curEnabled = not curEnabled
        self.ch1.SetFlagProportionalResizing( curEnabled )
        self.ch2.SetFlagProportionalResizing( curEnabled )
        self.l0.SetLabel( "proportional resizing (%d)" %(curEnabled) )

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

<p>Selections, bitmaps and sort arrows are optional</p>

<p>A limitation: text and bitmaps are mutually exclusive.</p>

<p>The MSW version of this control will have a persistant selection indicator. The native MSW control has no canonical selection UI, instead using a sort arrow to serve double-duty as a selection indicator; nonetheless, it has a rollover indicator.</p>

<p>The GTK framework lacks, or appears to lack, a native control: a simple bevel button shall suffice for the theme background.</p>

</body></html>
"""


if __name__ == '__main__':
    import sys,os
    import run
    run.main(['', os.path.basename(sys.argv[0])] + sys.argv[1:])

