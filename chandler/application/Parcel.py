"""
@copyright: Copyright (c) 2004-2006 Open Source Applications Foundation
@license: U{http://osafoundation.org/Chandler_0.1_license_terms.htm}
"""
__parcel__ = "//Schema/Core"

import sys, os, logging
from datetime import datetime

import schema, pkg_resources
from pkg_resources import working_set
import application.Globals as Globals

logger = logging.getLogger(__name__)

def activate_plugins(dirs, working_set=working_set):
    """
    Add plugins from `dirs` to `working_set`
    """
    plugin_env = pkg_resources.Environment(dirs)
    dists, errors = working_set.find_plugins(plugin_env, fallback=False)
    map(working_set.add, dists)
    # XXX log errors

def loadable_parcels(working_set=working_set, env=None, installer=None):
    """
    Yield entry points for loadable parcels in `working_set`
    """
    for ep in working_set.iter_entry_points('chandler.parcels'):
        try:
            ep.require(env, installer)
        except pkg_resources.ResolutionError:
            # XXX log the error
            continue    # skip unloadable parcels ???
        else:
            yield ep

def load_parcel_from_entrypoint(rv,ep):
    """
    Load the parcel defined by entrypoint `ep` into repository view `rv`

    `ep` should be an entry point yielded by ``loadable_parcels()``, and `rv`
    should be a repository view.  The egg corresponding to the entry point,
    along with any dependencies, must already be on sys.path.

    If a parcel already exists in `rv` for the entrypoint, it is updated if
    its version doesn't match the version of the egg containing the
    entry point.  If no parcel exists, it is created.
    """
    module_name = ep.module_name
    egg_version = ep.dist.version

    if ep.attrs:
        # This is a fatal error so that nobody will ship
        # a parcel with attrs set to something!
        raise AssertionError(
            "%s: parcel entrypoints must specify a module only"
            % ep.dist
        )

    old_parcel = rv.findPath('//parcels/'+module_name.replace('.','/'))

    if old_parcel is None:
        new_parcel = schema.parcel_for_module(module_name, rv)
        old_version = egg_version
    else:
        new_parcel = old_parcel
        old_version = getattr(old_parcel,'version','')

    #new_parcel.egg_id = ep.dist.key    XXX schema change needed for this
    new_parcel.version = egg_version

    # XXX what if parcel came from a different egg?

    if old_version <> egg_version:
        schema.synchronize(rv, module_name)     # get any new Kinds
        module = sys.modules[module_name]       # get the actual module
        if hasattr(module,'installParcel') and not hasattr(module,'__parcel__'):
            module.installParcel(new_parcel, old_version)   # upgrade!

    return new_parcel


#@@@Temporary testing tool written by Morgen -- DJA
timing = False
if timing: import util.timing

class Manager(schema.Item):
    """
    To use the parcel manager, retrieve an instance of it by using the class
    method get()::

        import application
        mgr = application.Parcel.Manager.get(view, path=parcelSearchPath)
        mgr.loadParcels()

    if "path" is not passed in, it will use
    os.path.join(Globals.chandlerDirectory, "parcels").
    """

    #The path attribute contains the path in bytes. These bytes
    #may be 8bit with a filesystem encoding or may be
    #7bit ascii
    path = schema.Sequence(schema.Bytes, initialValue = [])

    @classmethod
    def get(cls, view, path=None):
        """
        Class method for getting an instance of the parcel manager.

        If there is a manager item already already in this repository, that
        will be returned.  Otherwise one will be created.

        @param view: The repository view object to load items into.
        @type view: L{repository.persistence.RepositoryView}
        @param path: The search path for finding parcels.  This is a list
        of absolute directory paths; when loading parcels, each directory
        in the search path will be used as a starting point for recursively
        finding parcel.xml files.
        @type path: list
        @return: parcel manager object
        """

        parcelRoot = view.findPath("//parcels")
        if parcelRoot is None:
            parcelRoot = Parcel("parcels",view)

        manager = view.findPath("//parcels/manager")
        if manager is None:
            manager = Manager("manager", parcelRoot)

        if path:
            manager.path = path

        else:
            manager.path = [os.path.join(Globals.chandlerDirectory, "parcels")]

        return manager


    def __syncParcel(self, pkg):
        """
        Synchronize the specified parcel's Python schema with self.repo

        This will import the corresponding Python module and synchronize its
        schema with the repository.  If the imported module has a parent
        module that has not yet been synchronized, this method will load
        the parent parcel, thereby synchronizing the parent module first.
        """
        if pkg in self._imported:
            return  # skip already-processed parcels
        else:
            self._imported.add(pkg)

        if '.' in pkg:
            # load parent first - even though schema API does this too,
            # the parcel loader will get confused and not load the
            # parent parcel correctly, unless we process it here.  :(
            parent_pkg = pkg.rsplit('.',1)[0]
            if parent_pkg not in self._imported:
                self.__syncParcel(parent_pkg)

        # Last, but not least, actually synchronize the package
        schema.synchronize(self.itsView, pkg)


    def findPlugins(self):
        """
        Yield top-level parcels
        """
        from glob import glob
        for directory in self.path:
            for initfile in glob(os.path.join(directory,'*','__init__.py')):
                yield os.path.basename(os.path.dirname(initfile))


    def loadParcels(self, namespaces=None):
        """
        Load parcel items into the repository.

        The namespaces passed in via the namespaces parameter (a list) are
        then loaded into the repository.  If that parameter is None, then all
        parcels are loaded.

        @param namespaces: The list of namespaces to load
        @type namespaces: list of strings
        """
        #@@@Temporary testing tool written by Morgen -- DJA
        if timing: util.timing.begin("Load parcels")

        self._imported = set()    # imported namespaces

        load_plugins = not namespaces

        if not namespaces:
            namespaces = sorted(self.findPlugins())
            appParcel = getattr(
                getattr(Globals,'options',None), "appParcel", "osaf.app"
            )
            # always load the app parcel first
            namespaces.insert(0, appParcel)

        logger.info("Loading parcels...")

        # Load old-style or explicitly-listed parcels
        for namespace in namespaces:
            self.__syncParcel(namespace)

        if load_plugins:
            # Load egg and plugin parcels
            activate_plugins(self.path)
            for parcel_ep in loadable_parcels():
                load_parcel_from_entrypoint(self.itsView, parcel_ep)

        logger.info("...done")

        #@@@Temporary testing tool written by Morgen -- DJA
        if timing: util.timing.end("Load parcels")

        #if self.itsView._schema_init_level or self.itsView._schema_init_queue:
        #    raise AssertionError("Incomplete initialization")


# - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - -

class Parcel(schema.Item):
    """
    The parcel item class.
    """
    author = schema.One(schema.Text)
    publisher = schema.One(schema.Text)
    status = schema.One(schema.Text)
    summary = schema.One(schema.Text)
    icon = schema.One(schema.Text)
    version = schema.One(schema.Text)
    createdOn = schema.One(schema.DateTime)
    modifiedOn = schema.One(schema.DateTime)
    namespace = schema.One(schema.Text, defaultValue = u'')
    namespaceMap = schema.Mapping(schema.Text, initialValue = {})
    file = schema.One(schema.Text, initialValue = u'')
    originalValues = schema.Mapping(schema.Dictionary, initialValue = {})

    def __init__(self, *args, **kw):
        super(Parcel, self).__init__(*args, **kw)
        self.createdOn = datetime.now()
        self.modifiedOn = self.createdOn


# - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - -

class Reference(schema.Item):
    item = schema.One(
        schema.Item,
        initialValue = None,
        otherName = 'references'
    )

# - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - -

