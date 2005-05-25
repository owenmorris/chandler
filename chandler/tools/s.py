"""
A 'shortcuts' module for programmers in a hurry; it's named "s" so you can get
from zero-to-repository as fast as you can type:

>>> from tools.s import *

Afterwards, several variables will be bound to interesting objects such as
the repository (which will be created and 'packed' if it doesn't already exist
at chandler/__repository__), some repository items, and some handy methods.

Usage:

    * Via hardhat:
        % hardhat -i
        >>> from tools.s import *

    * Via RunPython:
        % RunPython -i tools/s.py

    * Within Chandler:
        Launch Chandler
        Menu: Test | Show PyCrust Debugger
        >>> from tools.s import *

    Once you've done one of the above, you can then do things like:

        >>> r.check() # repository validation check; if True: all good
        >>> lp("http://osafoundation.org/parcels/osaf/framework/blocks")
        >>> lp(CPIA) # same effect as previous line, i.e., load CPIA parcel
        >>> lp() # load all parcels
        >>> tree = pm.lookup(CPIA, "Tree") # fetch the blocks/Tree item
        >>> pp(tree) # pretty-print the item

"""
import os, sys
import application.Globals as Globals
import application.Parcel

# - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - -

def initRepository(directory, destroy=False):
    """
    Create an instance of a repository (or open one if existing)

    If the repository hasn't had its //Schema loaded, the schema.pack will
    get loaded.  Also the notification manager will be initialized.

    @param directory: The directory to use for the repository files
    @type directory: string
    @param destroy: If True, wipe out existing repository first (default=False)
    @type directory: boolean
    @return: the repository object
    """

    from repository.persistence.DBRepository import DBRepository
    rep = DBRepository(directory)

    kwds = { 'create' : True, 'recover' : True, 'refcounted' : True }
    if destroy:
        rep.create(**kwds)
    else:
        rep.open(**kwds)

    if rep.findPath("//Schema") is None:
        rep.loadPack(os.path.join(Globals.chandlerDirectory, 'repository',
         'packs', 'schema.pack'))
        rep.loadPack(os.path.join(Globals.chandlerDirectory, 'repository',
         'packs', 'chandler.pack'))

    return rep

def initLogger(file):
    """
    Set up the logging handler

    @param file: path to the file to log to
    @type file: string
    """

    import logging
    handler = logging.FileHandler(file)
    formatter = logging.Formatter('%(asctime)s %(levelname)s %(message)s')
    handler.setFormatter(formatter)
    logging.getLogger().addHandler(handler)

def initParcels(rep):
    """
    Load all parcels under the 'parcels' directory
    """

    parcelDir = os.path.join(Globals.chandlerDirectory, "parcels")
    parcelSearchPath = [ parcelDir ]
    sys.path.insert(1, parcelDir)

    """
    If PARCELDIR env var is set, put that
    directory into sys.path before any modules are imported.
    """
    debugParcelDir = None
    if os.environ.has_key('PARCELDIR'):
        path = os.environ['PARCELDIR']
        if path and os.path.exists(path):
            print "Using PARCELDIR environment variable (%s)" % path
            debugParcelDir = path
            sys.path.insert (2, debugParcelDir)
            parcelSearchPath.append( debugParcelDir )

    application.Parcel.Manager.get(rep.view,
                                   path=parcelSearchPath).loadParcels()

def setup(directory, destroy=False):
    """
    Prepare the repository, logger, and parcels

    @param directory: the directory to set Globals.chandlerDirectory to
    @type directory: string
    @param destroy: If True, wipe out existing repository first (default=False)
    @type destroy: boolean
    @return: the repository object
    """

    Globals.chandlerDirectory = directory
    initLogger(os.path.join(directory, 'chandler.log'))
    rep = initRepository(os.path.join(directory, '__repository__'), destroy)
    initParcels(rep)
    return rep

# - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - -

r = setup(os.environ['CHANDLERHOME'])
import osaf.framework.twisted.TwistedReactorManager as trm


# Bind some useful variables:
pm = application.Parcel.Manager.get(r.view)
Kind = r.findPath("//Schema/Core/Kind")
Item = r.findPath("//Schema/Core/Item")
parcels = r.findPath("//parcels")
CORE = application.Parcel.CORE
CPIA = application.Parcel.CPIA

# Handy dandy methods:
def pp(item, rec=False):
    application.Parcel.PrintItem(item.itsPath, item.itsView, rec)

def find(view, path):
    return view.findPath(path)

def lp(uri=None):
    if uri is None:
        application.Parcel.Manager.get(r.view).loadParcels()
    else:
        application.Parcel.Manager.get(r.view).loadParcels([uri])

def start():
    global twistedmgr
    twistedmgr = trm.TwistedReactorManager()
    twistedmgr.startReactor()
    print "Started webserver.  Be sure to stop() it before exiting."

def stop():
    global twistedmgr
    twistedmgr.stopReactor()
    print "Stopped webserver."

import osaf.contentmodel.ContentModel as cm
import osaf.contentmodel.calendar.Calendar as cal
import osaf.contentmodel.contacts.Contacts as con
import datetime as dt

print """
Shortcuts loaded:
r = repository
Kind = //Schema/Core/Kind item
Item = //Schema/Core/Item item
parcels = //parcels item
pm = parcel manager
pp(item) = pretty printer (application.Parcel.PrintItem)
find(view, path) = view.findPath(path)
lp(uri) = load a parcel, given its uri; if uri is None, load all parcels

Modules loaded:
cm = osaf.contentmodel.ContentModel
cal = osaf.contentmodel.calendar.Calendar
con = osaf.contentmodel.contacts.Contacts

Have fun"""
