import Pyblosxom.entries.base

def verify_installation(request):
    config = request.getConfiguration()

    if not config.get('chandler_plugin_enable', False):
        # Not running inside chandler, pretend we're not here.
        return 1

    # what sort of verification shall we do here?
    return 1

class PyblChandler:
    """ Not used yet """

    def __init__(self, request):
        self._request = request

    def __str__(self):
        return "Chandler rocks"

class FakeCgiField(object):
    """ Pyblosxom used the cgi module to look for the 'flav' query parameter,
        so we're simulating a cgi field object. """
    def __init__(self, name, value):
        self.name = name
        self.value = value

def cb_pathinfo(args):
    # Here is where we figure out our query, based on the request uri
    request = args["request"]
    config = request.getConfiguration()

    if not config.get('chandler_plugin_enable', False):
        # Not running inside chandler, pretend we're not here.
        return

    data = request.getData()
    pyhttp = request.getHttp()

    # Here is our chance to overwrite the cgi variables that the standard
    # handler inject into pyhttp
    pyhttp['form'] = {}
    for (key, value) in data['chandlerRequest'].args.iteritems():
        pyhttp['form'][key] = FakeCgiField(key, value[0])


class BlogEntry(Pyblosxom.entries.base.EntryBase):
    def __init__(self, request):
        Pyblosxom.entries.base.EntryBase.__init__(self, request)
        self._metadata = {}
        self._data = None

    def getId(self):
        return self._UUID

    def setItem(self, item):
        self._item = item
        self._UUID = item.itsUUID
        self.setTime( item.date.tuple() )
        self.setMetadata('title', item.about)
        self.setData('The body needs to go here.  This is an entry about %s' % item.about)

    def setData(self, data):
        self._data = data

    def getData(self):
        return self._data

    def setMetadata(self, key, value):
        self._metadata[key] = value

    def getMetadata(self, key, default=None):
        return self._metadata.get(key, default)

def cb_filelist(args):
    """
    Here is where we populate the entry list
    """
    request = args["request"]
    config = request.getConfiguration()
    data = request.getData()
    pyhttp = request.getHttp()

    if not config.get('chandler_plugin_enable', False):
        # Not running inside chandler, pretend we're not here.
        return

    if config.get('chandler_plugin_mode', 'file') == 'file':
        # Running inside chandler, but serving file-based content
        return

    entryList = []
    import application.Globals
    from repository.item.Query import KindQuery
    noteKind = application.Globals.repository.findPath("//parcels/osaf/contentmodel/Note")
    for note in KindQuery().run([noteKind]):
        print "Found item:", note.itsPath
        newEntry = BlogEntry(request)
        newEntry.setItem(note)
        entryList.append(newEntry)

    return entryList


def cb_renderer(args):
    """ We'll be using the blosxom renderer, but instantiating one using
        a file-like object that the Chandler Blog servlet has passed in via
        the data dict, using key 'chandlerOutput'
    """
    request = args["request"]
    config = request.getConfiguration()

    if not config.get('chandler_plugin_enable', False):
        # Not running inside chandler, pretend we're not here.
        return

    data = request.getData()
    from Pyblosxom.renderers.blosxom import Renderer
    return Renderer(request, data['chandlerOutput'])
