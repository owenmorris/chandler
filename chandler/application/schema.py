from repository.persistence.RepositoryView import nullRepositoryView as nrv
from application.Parcel import Manager, Parcel

import __main__
defaultGlobalDict = __main__.__dict__

import os, repository, threading
packdir = os.path.join(os.path.dirname(repository.__file__),'packs')    # XXX
global_lock = threading.RLock()

if nrv.findPath('//Schema/Core/Item') is None:
    nrv.loadPack(os.path.join(packdir,'schema.pack'))
if nrv.findPath('//Schema/Core/Parcel') is None:
    nrv.loadPack(os.path.join(packdir,'chandler.pack'))

def importString(name, globalDict=defaultGlobalDict):
    """Import an item specified by a string

    Example Usage::

        attribute1 = importString('some.module:attribute1')
        attribute2 = importString('other.module:nested.attribute2')

    'importString' imports an object from a module, according to an
    import specification string: a dot-delimited path to an object
    in the Python package namespace.  For example, the string
    '"some.module.attribute"' is equivalent to the result of
    'from some.module import attribute'.

    For readability of import strings, it's sometimes helpful to use a ':' to
    separate a module name from items it contains.  It's optional, though,
    as 'importString' will convert the ':' to a '.' internally anyway.

    This routine was copied from PEAK's ``peak.util.imports`` module.
    """

    if ':' in name:
        name = name.replace(':','.')

    path  = []

    for part in filter(None,name.split('.')):
        if path:
            try:
                item = getattr(item, part)
                path.append(part)
                continue
            except AttributeError:
                pass

        path.append(part)
        item = __import__('.'.join(path), globalDict, globalDict, ['__name__'])

    return item


def parcel_for_module(moduleName):
    """Return the Parcel for the named module 

    If the named module has a ``__parcel__`` attribute, its value will be
    returned.  If the module does not have a ``__parcel__``, then a new parcel
    will be created and stored in the module's ``__parcel__`` attribute.  If
    the module has a ``__parcel_class__`` attribute, it will be used in place
    of the ``application.Parcel.Parcel`` class, to create the parcel instance.
    The ``__parcel_class__`` must accept three arguments: the parcel's name,
    its parent parcel (which will be the ``parcel_for_module()`` of the
    module's enclosing package), and the Parcel Kind (as found at
    ``//Schema/Core/Parcel`` in the null repository view).

    If ``moduleName`` is an empty string, the ``//parcels`` root of the null
    repository view is returned.

    This routine is thread-safe and re-entrant.
    """
    global_lock.acquire()
    try:
        if moduleName:
            module = importString(moduleName)
            try:
                return module.__parcel__
            except AttributeError:
                if '.' in moduleName:
                    parentName,modName = moduleName.rsplit('.',1)
                else:
                    parentName,modName = '',moduleName
                mkParcel = getattr(module,'__parcel_class__',Parcel)
                module.__parcel__ = parcel = mkParcel(
                    modName, parcel_for_module(parentName),
                    nrv.findPath('//Schema/Core/Parcel')
                )
                return parcel
        else:    
            root = nrv.findPath('//parcels')
            if root is None:
                Manager.get(nrv,["x"])  # force setup of parcels root
                root = nrv.findPath('//parcels')
            return root
    finally:
        global_lock.release()
