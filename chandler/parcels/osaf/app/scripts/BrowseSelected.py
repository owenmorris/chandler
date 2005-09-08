# prints the item that's currently selected.

import osaf.framework.blocks.Block as Block
import webbrowser

f = Block.Block.getFocusBlock()
try:
  i = f.selectedItemToView
except AttributeError:
  i = f.selection

if i:
    path = str(i.itsPath)[1:]
    url = 'http://localhost:1888/repo%s' % path
    webbrowser.open(url)
