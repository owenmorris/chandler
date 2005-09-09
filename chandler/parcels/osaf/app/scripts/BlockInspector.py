# prints the block found under the cursor

import wx
w = wx.FindWindowAtPoint(wx.GetMousePosition())
while not hasattr(w, 'blockItem'):
    w = w.GetParent()
print w.blockItem.blockName, w.blockItem


