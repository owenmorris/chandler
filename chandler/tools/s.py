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
import os
import application.Globals
import application.Parcel


r = application.Globals.repository

if r is None:
    from repository.persistence.XMLRepository import XMLRepository

    # No matter our cwd, or sys.argv[0], locate the chandler directory:
    home = \
     os.path.dirname(os.path.dirname(os.path.abspath(application.__file__)))

    application.Globals.chandlerDirectory = home
    r = XMLRepository(os.path.join(home, "__repository__"))
    r.open(create=True)
    if r.findPath("//Schema") is None:
        r.loadPack(
         os.path.join(home, "repository", "packs", "schema.pack")
        )
    application.Globals.repository = r

# Bind some useful variables:
pm = application.Parcel.Manager.getManager()
Kind = r.findPath("//Schema/Core/Kind")
Item = r.findPath("//Schema/Core/Item")
parcels = r.findPath("//parcels")
CORE = application.Parcel.CORE
CPIA = application.Parcel.CPIA

# Handy dandy methods:
def pp(item, rec=False):
    application.Parcel.PrintItem(item.itsPath, application.Globals.repository, rec)

def find(path):
    return application.Globals.repository.findPath(path)

def lp(uri=None):
    if uri is None:
        application.Parcel.Manager.getManager().loadParcels()
    else:
        application.Parcel.Manager.getManager().loadParcels([uri])

print """
Shortcuts loaded:
r = repository
Kind = //Schema/Core/Kind item
Item = //Schema/Core/Item item
parcels = //parcels item
pm = parcel manager
pp(item) = pretty printer (application.Parcel.PrintItem)
find(path) = repository.findPath(path)
lp(uri) = load a parcel, given its uri; if uri is None, load all parcels

Have fun"""
