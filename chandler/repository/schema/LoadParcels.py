""" Parcel loading"""

__revision__  = "$Revision$"
__date__      = "$Date$"
__copyright__ = "Copyright (c) 2003 Open Source Applications Foundation"
__license__   = "http://osafoundation.org/Chandler_0.1_license_terms.htm"

import os, string, logging

import mx.DateTime as DateTime

from repository.schema.ParcelLoader import ParcelLoader
from repository.schema.Parcel import Parcel
from repository.persistence.Repository import RepositoryError


def LoadDependency(repository, uri, searchPath):
    # Easy success if we find the parcel
    parcel = repository.find(uri)
    if parcel: return

    # Look for the parcel anywhere on the path
    file = FindParcelFile(uri, searchPath)
    loader = ParcelLoader(repository, LoadDependency, searchPath)
    loader.load(file, uri)
    logging.debug("Loaded the dependency %s" % file)

def FindParcelFile(uri, searchPath):
    path = ""
    uri = string.lstrip(uri, "//Parcels")
    for part in string.split(uri, '/'):
        path = os.path.join(path, part)
    path = os.path.join(path, 'parcel.xml')
    file = SearchFile(path, searchPath)
    return file

def SearchFile(filePath, searchPath):
    for path in string.split(searchPath, os.pathsep):
        candidate = os.path.join(path, filePath)
        if os.path.exists(candidate):
            return os.path.abspath(candidate)
    raise IOException, "File not found %s" % filePath

def WalkParcels(parcel):
    yield parcel
    for part in parcel:
        if isinstance(part, Parcel):
            for subparcel in WalkParcels(part):
                yield subparcel

def LoadParcels(searchPath, repository):

    Parcel.setupParcels(repository)
    loader = ParcelLoader(repository, LoadDependency, searchPath)

    for directory in string.split(searchPath, os.pathsep):
        for root, dirs, files in os.walk(directory):
            if 'parcel.xml' in files:
                uri = "//Parcels/%s" % string.lstrip(root, directory)
                uri = uri.replace(os.path.sep, "/")
                parcel = repository.find(uri)
                path = os.path.join(root, 'parcel.xml')
                if ((not parcel) or
                    (parcel.modifiedOn.ticks() < os.stat(path).st_mtime)):
                    try:
                        loader.load(path, uri)
                        if parcel:
                            logging.warning("Reloaded the parcel %s" % path)
                            parcel.modifiedOn = DateTime.now()
                    except Exception, e:
                        logging.exception("Failed to load parcel %s" % path)
                        try:
                            repository.cancel()
                        except:
                            logging.exception("repository.cancel() failed")
                            raise RepositoryError, "See log for exceptions"
                    else:
                        logging.debug("Loaded the parcel %s" % path)
                        repository.commit()

    root = repository.find("//Parcels")
    for parcel in WalkParcels(root):
        parcel.startupParcel()
