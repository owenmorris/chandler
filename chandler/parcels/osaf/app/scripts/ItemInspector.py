# prints the item that's currently selected.

import osaf.framework.blocks.Block as Block

f = Block.Block.getFocusBlock()
try:
  i = f.selectedItemToView
except AttributeError:
  i = f.selection
print i.displayName.encode('utf8'), repr(i)
