"""
@copyright: Copyright (c) 2004 Open Source Applications Foundation
@license: U{http://osafoundation.org/Chandler_0.1_license_terms.htm}
"""

"""
application.Util is a module for setting up various parts of the Chandler
framework
"""

import os, sys
import application.Globals as Globals

# - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - -

def repository(directory, destroy=False):
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

    from repository.persistence.XMLRepository import XMLRepository
    rep = XMLRepository(directory)

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
    Globals.repository = rep

    # Notification manager is now needed for Item Collections(?):
    from osaf.framework.notifications.NotificationManager \
     import NotificationManager
    Globals.notificationManager = NotificationManager()

def logger(file):
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

def parcels():
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

    from application.Parcel import Manager
    manager = Manager.getManager(path=parcelSearchPath)
    manager.loadParcels()

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
    logger(os.path.join(directory, 'chandler.log'))
    repository(os.path.join(directory, '__repository__'), destroy)
    parcels()
    return Globals.repository

# - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - -
