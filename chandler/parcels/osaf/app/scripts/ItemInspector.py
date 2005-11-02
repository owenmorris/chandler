# prints the item that's currently selected.

import osaf.framework.blocks.Block as Block

f = Block.Block.getFocusBlock()
i = getattr(f, "selectedItemToView", None)
if i is None:
    try:
        i = f.selection[0]
    except (IndexError, AttributeError):
        i = None
if i is not None:
  print i.displayName.encode('utf8'), repr(i)
else:
  print None