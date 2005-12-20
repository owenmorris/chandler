# prints the item that's currently selected.

import osaf.framework.blocks.Block as Block
from osaf import webserver
import webbrowser

f = Block.Block.getFocusBlock()
i = getattr(f, "selectedItemToView", None)
if i is None:
    try:
        i = f.selection[0]
    except (IndexError, AttributeError):
        i = None
if i is not None:
    for server in webserver.Server.iterItems(i.itsView):
        if not server.isActivated():
            server.startup()
    #XXX [i18n] i.itsPath should be an ascii string however
    #    it is a repository.util.Path.Path.
    #    In addition when doing an str() or i.itsPath
    #    in certain cases the value returned is unicode.
    #    This is not correct and needs to be fixed.
    #    This hack handles the case where the path is returned as
    #    unicode.

    path = unicode(i.itsPath)[1:]

    url = 'http://localhost:1888/repo%s' % path.encode('utf8')
    webbrowser.open(url)
