__version__ = "$Revision: 5915 $"
__date__ = "$Date: 2005-07-09 11:49:30 -0700 (Sat, 09 Jul 2005) $"
__copyright__ = "Copyright (c) 2003-2005 Open Source Applications Foundation"
__license__ = "http://osafoundation.org/Chandler_0.1_license_terms.htm"


import sys, os
from types import GeneratorType
from code import interact

import application.Utility as Utility
import application.Globals as Globals
from repository.item.Item import Item

view = None
reactorManager = None
wakeupCaller = None


def startup(**kwds):
    global view

    Globals.chandlerDirectory = Utility.locateChandlerDirectory()
    if not Globals.chandlerDirectory:
        print "Please set CHANDLERHOME"
        return None
    os.chdir(Globals.chandlerDirectory)

    Utility.initLocale('en')

    Globals.options = Utility.initOptions(Globals.chandlerDirectory, **kwds)
    profileDir = Globals.options.profileDir

    logFile = os.path.join(profileDir, 'chandler.log')
    Utility.initLogging(logFile)

    parcelPath = Utility.initParcelEnv(Globals.chandlerDirectory,
                                       Globals.options.parcelPath)

    view = Utility.initRepository(Utility.locateRepositoryDirectory(profileDir),
                                  Globals.options)

    if not Utility.verifySchema(view):
        print "Schema mismatch.  Try again with startup(create=True)"
        return None

    Utility.initCrypto(Globals.options.profileDir)
    Utility.initParcels(view, parcelPath)

    return view

def go():
    global reactorManager, wakeupCaller

    print "Igniting Twisted reactor..."
    view.commit()
    reactorManager = Utility.initTwisted()
    wakeupCaller = Utility.initWakeup(view)
    print "...ready"

def shutdown():
    if wakeupCaller is not None:
        Utility.stopWakeup(wakeupCaller)
    if reactorManager is not None:
        Utility.stopTwisted(reactorManager)
    Utility.stopRepository(view)
    Utility.stopCrypto(Globals.options.profileDir)


def setDisplayHook():
    """
    Install a custom displayhook to keep Python from setting the global
    _ (underscore) to the value of the last evaluated expression.  If
    we don't do this, our mapping of _ to gettext can get overwritten.
    """
    def _displayHook(obj):
        if obj is not None:
            print repr(obj)

    sys.displayhook = _displayHook



# Repository-as-file-system commands:

currentItem = None
currentList = None

def _argToItem(arg):
    global currentItem

    if currentItem is None:
        currentItem = view

    if arg is None:
        return currentItem

    # arg is a number
    if isinstance(arg, (int, long)):
        try:
            return currentList[arg-1]
        except:
            return None

    # arg is an Item
    elif isinstance(arg, Item):
        return arg

    # arg is a string (path, either absolute or relative to currentItem)
    else:
        return currentItem.findPath(arg)

def getKind(kindName):
    kindKind = view.findPath("//Schema/Core/Kind")
    matching = []
    for kind in kindKind.iterItems():
        if kind.itsName == kindName:
            matching.append(kind)
    if len(matching) == 0:
        return None
    return matching[0]

def ofKind(kindName, recursive=True):
    kind = getKind(kindName)
    for item in kind.iterItems(recursive=recursive):
        yield item

def create(kindName):
    kind = getKind(kindName)
    return kind.newItem()

def cd(arg):
    global currentItem

    item = _argToItem(arg)

    if item is not None:
        currentItem = item
        print "Current item:", item.itsPath
    else:
        print "no matching item"

def pwd():
    global currentItem

    if currentItem is None:
        currentItem = view

    print currentItem.itsPath

def ls(arg=None):
    global currentList


    if isinstance(arg, GeneratorType):
        currentList = []
        for item in arg:
            currentList.append(item)
    else:
        item = _argToItem(arg)
        currentList = []
        for child in item.iterChildren():
            currentList.append(child)

    currentList.sort(lambda x, y: cmp(str(x.getItemDisplayName()).lower(), str(y.getItemDisplayName()).lower()))

    count = 1
    for item in currentList:
        kind = item.itsKind
        if kind is None:
            kindName = "<Kindless>"
        else:
            kindName = kind.getItemDisplayName()
        print "%3d. %s (%s)" % (count,
                                item.getItemDisplayName(),
                                kindName)
        count += 1

def grab(arg=None):
    return _argToItem(arg)


def show(arg=None, recursive=False):
    item = _argToItem(arg)

    item.printItem(recursive)


def readme():
    print """
This is a version of Chandler which doesn't start up the wx portion
of the code.  The repository has been opened, and packs and parcels
loaded. If you want to start Twisted services (including WakeupCallers),
you need to run the 'go( )' method from the shell.  Once you've
done that any registered web servlets will then be availalbe at
http://localhost:1888/

This script accepts all of the command-line arguments and environment
variables as the GUI Chandler, as they share the same option-parsing
code.  Exiting the interactive session (by Control-D on *nix boxes,
and by Control-Z followed by Enter on Windows) will shut down
twisted, commit the repository, and exit the program.

Some helper methods have been defined to make it easy to move around within
the repository:  cd, pwd, ls, grab, show

- cd(item or repository path or list number)
    Either pass in an item, a path string like "//userdata", or the number of
    an item as displayed in the most recent ls() call

- pwd()
    Prints the repository path of the "current" item (the item you last
    cd'ed to)

- ls(item or repository path or list number or iterator or None)
    Lists all the child items of the argument, which is either an item,
    a repository path, a previous ls() number, an iterator, or None which
    will use the "current" item

- grab(item or repository path or list number or None)
    Returns the item corresponding to the argument, which can be an item,
    a repository path, or a previous ls() number, or None which will return
    the "current" item

- show(item or list number or repository path or None, recursive=False)
    Prints out the attributes of an item, and the argument can be an item,
    a number from the most recent ls(), a repository path, or if nothing
    is passed in it will use the "current" item.  There is an optional
    'recursive' boolean argument which defaults to False.

- create(kind name)
    Creates and returns an item of the kind 'kind name'

- getKind(kind name)
    Returns the kind with that name

- ofKind(kind name)
    Returns an iterator of all items of that kind; nest this within an ls()
    call like:  ls( ofKind("RSSItem") )


"""

def main():
    print "Starting up..."
    view = startup()
    if not view:
        sys.exit(1)
    setDisplayHook()

    banner = "\nWelcome!  Headless Chandler will shut down when you " \
             "exit this Python session.\n" \
             "The variable, 'view', is now set to the main repository " \
             "view.\n" \
             "Type 'go()' to fire up Twisted services, or 'readme()' for " \
             "more info."

    script = Globals.options.script
    if script:
        try:
            if script.endswith('.py'):
                file = open(script)
                script = file.read()
                file.close()

            exec script in globals()
        except Exception, e:
            shutdown()
            raise e
        else:
            shutdown()

    else:
        interact(banner,
                 None,
                 { "__name__" : "__console__",
                   "__doc__"    : None,
                   "view"       : view,
                   "readme"     : readme,
                   "go"         : go,
                   "cd"         : cd,
                   "pwd"        : pwd,
                   "ls"         : ls,
                   "grab"       : grab,
                   "show"       : show,
                   "create"     : create,
                   "getKind"    : getKind,
                   "ofKind"     : ofKind,
                 })

        print "Shutting down..."
        shutdown()


if __name__ == "__main__":
    main()
