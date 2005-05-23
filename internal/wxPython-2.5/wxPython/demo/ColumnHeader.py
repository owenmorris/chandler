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
        self.baseWidth1 = 350
        self.baseWidth2 = 270
        self.colHeight = 20
        self.colStartX = 175
        self.colStartY = 20

        self.stepSize = 0
        self.stepDir = -1

        # "no" to sort arrows for this list
        self.baseCntlID = 1001
        prompt = "ColumnHeader (%d)" %(self.baseCntlID)
        l1 = wx.StaticText( self, -1, prompt, (self.colStartX, self.colStartY), (200, 20) )

        ch1 = wx.colheader.ColumnHeader( self, self.baseCntlID, (self.colStartX, self.colStartY + 20), (self.baseWidth1, self.colHeight), 0 )
        dow = [ "Sun", "Mon", "Tue", "Wed", "Thu", "Fri", "Sat" ]
        for v in dow:
            ch1.AddItem( -1, v, wx.colheader.CH_JUST_Center, 50, 0, 0, 1 )
        ch1.SetSelectedItem( 0 )
        self.ch1 = ch1
        self.Bind( wx.colheader.EVT_COLUMNHEADER_SELCHANGED, self.OnClickColumnHeader, ch1 )
        #ch1.SetToolTipString( "ColumnHeader (%d)" %(self.baseCntlID) )

        # "yes" to sort arrows for this list
        prompt = "ColumnHeader (%d)" %(self.baseCntlID + 1)
        l2 = wx.StaticText( self, -1, prompt, (self.colStartX, self.colStartY + 80), (200, 20) )

        ch2 = wx.colheader.ColumnHeader( self, self.baseCntlID + 1, (self.colStartX, self.colStartY + 100), (self.baseWidth2, self.colHeight), 0 )
        coffeeNames = [ "Juan", "Valdez", "coffee guy" ]
        for i, v in enumerate( coffeeNames ):
            ch2.AddItem( -1, v, wx.colheader.CH_JUST_Left + i, 90, 0, 1, 1 )
        ch2.SetSelectedItem( 0 )

        self.ch2 = ch2
        self.Bind( wx.colheader.EVT_COLUMNHEADER_SELCHANGED, self.OnClickColumnHeader, ch2 )
        #ch2.SetToolTipString( "ColumnHeader (%d)" %(cntlID) )

        # add demo UI controls
        miscControlsY = 190
        self.colStartX = 10

        cb1 = wx.CheckBox( self, -1, "Enable", (self.colStartX, miscControlsY), (100, 20), wx.NO_BORDER )
        self.Bind( wx.EVT_CHECKBOX, self.OnTestEnableCheckBox, cb1 )
        cb1.SetValue( ch1.IsEnabled() )

        cb2 = wx.CheckBox( self, -1, "Generic Renderer", (self.colStartX, miscControlsY + 25), (150, 20), wx.NO_BORDER )
        self.Bind( wx.EVT_CHECKBOX, self.OnTestGenericRendererCheckBox, cb2 )
        cb2.SetValue( ch1.GetAttribute( wx.colheader.CH_ATTR_GenericRenderer ) )

        cb3 = wx.CheckBox( self, -1, "Visible Selection", (self.colStartX, miscControlsY + 50), (150, 20), wx.NO_BORDER )
        self.Bind( wx.EVT_CHECKBOX, self.OnTestVisibleSelectionCheckBox, cb3 )
        cb3.SetValue( ch1.GetAttribute( wx.colheader.CH_ATTR_VisibleSelection ) )

        cb4 = wx.CheckBox( self, -1, "Proportional Resizing", (self.colStartX, miscControlsY + 75), (200, 20), wx.NO_BORDER )
        self.Bind( wx.EVT_CHECKBOX, self.OnTestProportionalResizingCheckBox, cb4 )
        cb4.SetValue( ch1.GetAttribute( wx.colheader.CH_ATTR_ProportionalResizing ) )

        if (ch1.GetAttribute( wx.colheader.CH_ATTR_Unicode )):
                prompt = "Unicode build"
        else:
                prompt = "ANSI build"
        l1 = wx.StaticText( self, -1, prompt, (self.colStartX, miscControlsY + 150), (150, 20) )

        l0O = wx.StaticText( self, -1, "Last action:", (self.colStartX, miscControlsY + 175), (90, 20) )
        l0 = wx.StaticText( self, -1, "[result]", (self.colStartX + 95, miscControlsY + 175), (250, 20) )
        self.l0 = l0

        btn = wx.Button( self, -1, "Delete Selection", (10, self.colStartY + 15) )
        self.Bind( wx.EVT_BUTTON, self.OnButtonTestDeleteItem, btn )

        btn = wx.Button( self, -1, "Add Bitmap Item", (10, self.colStartY + 80 + 5) )
        self.Bind( wx.EVT_BUTTON, self.OnButtonTestAddBitmapItem, btn )

        btn = wx.Button( self, -1, "Resize Division", (10, self.colStartY + 80 + 5 + 30) )
        self.Bind( wx.EVT_BUTTON, self.OnButtonTestResizeDivision, btn )

        self.colStartX += 165

        btn = wx.Button( self, -1, "Deselect", (self.colStartX, miscControlsY) )
        self.Bind( wx.EVT_BUTTON, self.OnButtonTestDeselect, btn )

        btn = wx.Button( self, -1, "Resize Bounds", (self.colStartX, miscControlsY + 30) )
        self.Bind( wx.EVT_BUTTON, self.OnButtonTestResizeBounds, btn )

        self.colStartX += 150

        styleList = ['None', 'Native', 'BoldLabel', 'ColourLabel', 'Grey', 'InvertBevel', 'Underline', 'Overline', 'Frame', 'Bullet']
        wx.StaticText( self, -1, "Selection Style:", (self.colStartX, miscControlsY + 0), (150, -1) )
        choice = wx.Choice( self, -1, (self.colStartX, miscControlsY + 20), choices = styleList )
        choice.SetSelection( ch1.GetSelectionDrawStyle() )
        self.Bind( wx.EVT_CHOICE, self.OnEvtChoiceSelectionStyle, choice )

        styleList = ['None', 'Left', 'Right', 'Up', 'Down']
        wx.StaticText( self, -1, "Arrow Button Style:", (self.colStartX, miscControlsY + 50), (150, -1) )
        choice = wx.Choice( self, -1, (self.colStartX, miscControlsY + 70), choices = styleList )
        itemIndex = self.ch2.GetSelectedItem()
        if ((itemIndex >= 0) and (itemIndex < self.ch2.GetItemCount())):
            choice.SetSelection( self.ch2.GetArrowButtonStyle( itemIndex ) )
        self.Bind( wx.EVT_CHOICE, self.OnEvtChoiceArrowButton, choice )
        self.choiceAB = choice

        self.colStartX = 175

    def OnClickColumnHeader( self, event ):
        ch = event.GetEventObject()
        self.l0.SetLabel( "(%d): clicked - selected (%ld)" %(event.GetId(), ch.GetSelectedItem()) )
        if (ch.GetId() == self.baseCntlID + 1):
            self.choiceAB.SetSelection( ch.GetSelectedItem() - 1 )
        # self.log.write( "Click! (%ld)\n" % event.GetEventType() )

    def OnButtonTestResizeBounds( self, event ):
        if (self.stepSize == 1):
            self.stepDir = (-1)
        else:
            if (self.stepSize == (-1)):
                self.stepDir = 1
        self.stepSize = self.stepSize + self.stepDir
        ch = self.ch1
        newSize = self.baseWidth1 + 40 * self.stepSize
        ch.DoSetSize( self.colStartX, self.colStartY + 20, newSize, 20, 0 )
        ch = self.ch2
        newSize = self.baseWidth2 + 40 * self.stepSize
        ch.DoSetSize( self.colStartX, self.colStartY + 100, newSize, 20, 0 )
        self.l0.SetLabel( "(both): resized bounds by (%d)" %(40 * self.stepSize) )

    def OnButtonTestDeleteItem( self, event ):
        ch = self.ch1
        itemIndex = ch.GetSelectedItem()
        if (itemIndex >= 0):
            ch.DeleteItem( itemIndex )
            self.baseWidth1 -= 70
            self.l0.SetLabel( "(%d): deleted item (%d)" %(ch.GetId(), itemIndex) )
        else:
            self.l0.SetLabel( "(%d): no item selected" %(ch.GetId()) )

    def OnButtonTestDeselect( self, event ):
        self.ch1.SetSelectedItem( -1 )
        self.ch2.SetSelectedItem( -1 )
        self.l0.SetLabel( "(both): deselected items" )

    def OnButtonTestAddBitmapItem( self, event ):
        ch = self.ch2
        itemCount = ch.GetItemCount()
        if (itemCount <= 8):
             itemIndex = ch.GetSelectedItem()
             if (itemIndex < 0):
                 itemIndex = itemCount
             ch.AddItem( itemIndex, "", wx.colheader.CH_JUST_Center, 40, 0, 0, 1 )
             ch.SetItemAttribute( itemIndex, wx.colheader.CH_ITEM_ATTR_FixedWidth, 1 )
             testBmp = images.getTest2Bitmap()
             ch.SetBitmapRef( itemIndex, testBmp )
             ch.SetSelectedItem( itemIndex )
             ch.ResizeToFit()
             self.baseWidth2 += 40
             self.l0.SetLabel( "(%d): added bitmap item (%d)" %(ch.GetId(), itemIndex) )
        else:
             self.l0.SetLabel( "(%d): enough items!" %(ch.GetId()) )

    def OnButtonTestResizeDivision( self, event ):
        ch = self.ch2
        itemIndex = ch.GetSelectedItem()
        if ((itemIndex > 0) and (itemIndex < ch.GetItemCount())):
            curExtent = ch.GetUIExtent( itemIndex )
            ch.ResizeDivision( itemIndex, curExtent.x - 5 )
            self.l0.SetLabel( "(%d): resized btw. %d and %d" %(ch.GetId(), itemIndex - 1, itemIndex) )
        else:
            self.l0.SetLabel( "(%d): no valid item selected" %(ch.GetId()) )

    def OnTestEnableCheckBox( self, event ):
        curEnabled = self.ch1.IsEnabled()
        curEnabled = not curEnabled
        self.ch1.Enable( curEnabled )
        self.ch2.Enable( curEnabled )
        self.l0.SetLabel( "enabled (%d)" %(curEnabled) )

    def OnTestGenericRendererCheckBox( self, event ):
        curEnabled = self.ch1.GetAttribute( wx.colheader.CH_ATTR_GenericRenderer )
        curEnabled = not curEnabled
        self.ch1.SetAttribute( wx.colheader.CH_ATTR_GenericRenderer, curEnabled )
        self.ch2.SetAttribute( wx.colheader.CH_ATTR_GenericRenderer, curEnabled )
        self.l0.SetLabel( "generic renderer (%d)" %(curEnabled) )

    def OnTestVisibleSelectionCheckBox( self, event ):
        curEnabled = self.ch1.GetAttribute( wx.colheader.CH_ATTR_VisibleSelection )
        curEnabled = not curEnabled
        self.ch1.SetAttribute( wx.colheader.CH_ATTR_VisibleSelection, curEnabled )
        self.ch2.SetAttribute( wx.colheader.CH_ATTR_VisibleSelection, curEnabled )
        self.l0.SetLabel( "selection visible (%d)" %(curEnabled) )

    def OnTestProportionalResizingCheckBox( self, event ):
        curEnabled = self.ch1.GetAttribute( wx.colheader.CH_ATTR_ProportionalResizing )
        curEnabled = not curEnabled
        self.ch1.SetAttribute( wx.colheader.CH_ATTR_ProportionalResizing, curEnabled )
        self.ch2.SetAttribute( wx.colheader.CH_ATTR_ProportionalResizing, curEnabled )
        self.l0.SetLabel( "proportional resizing (%d)" %(curEnabled) )

    def OnEvtChoiceSelectionStyle( self, event ):
        ch = event.GetEventObject()
        self.ch1.SetSelectionDrawStyle( event.GetSelection() )
        self.ch2.SetSelectionDrawStyle( event.GetSelection() )
        self.l0.SetLabel( "SelectionDrawStyle item (%d - %s)" %(event.GetSelection(), event.GetString()) )

    def OnEvtChoiceArrowButton( self, event ):
        ch = event.GetEventObject()
        itemIndex = self.ch2.GetSelectedItem()
        if ((itemIndex >= 0) and (itemIndex < self.ch2.GetItemCount())):
            self.ch2.SetArrowButtonStyle( itemIndex, event.GetSelection() )
        self.l0.SetLabel( "ArrowButton item (%d - %s)" %(event.GetSelection(), event.GetString()) )

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

<p>Selections, bitmaps, button arrows and sort arrows are optional</p>

<p>NB: not all of the selection styles are implemented</p>

<p>A limitation: text and bitmaps are mutually exclusive.</p>

<p>The MSW version of this control will have a persistant selection indicator. The native MSW control has no canonical selection UI, instead using a sort arrow to serve double-duty as a selection indicator; nonetheless, it has a rollover indicator.</p>

<p>The GTK framework lacks, or appears to lack, a native control: a simple bevel button shall suffice for the theme background.</p>

</body></html>
"""


if __name__ == '__main__':
    import sys,os
    import run
    run.main(['', os.path.basename(sys.argv[0])] + sys.argv[1:])

