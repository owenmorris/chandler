""" Parcel loading"""

__revision__  = "$Revision$"
__date__      = "$Date$"
__copyright__ = "Copyright (c) 2003 Open Source Applications Foundation"
__license__   = "http://osafoundation.org/Chandler_0.1_license_terms.htm"

import os, string, logging

import mx.DateTime as DateTime

from repository.parcel.ParcelLoader import ParcelLoader
from repository.parcel.Parcel import Parcel
from repository.persistence.RepositoryError import RepositoryError

from repository.item.Query import KindQuery

def LoadDependency(repository, uri, searchPath):
    # Easy success if we find the parcel
    parcel = repository.findPath(uri)
    if parcel: return

    # Look for the parcel anywhere on the path
    file = FindParcelFile(uri, searchPath)
    loader = ParcelLoader(repository, LoadDependency, searchPath)
    loader.load(file, uri)
    logging.debug("Loaded the dependency %s" % file)

def FindParcelFile(uri, searchPath):
    path = ""
    uri = uri[10:] # strip out "//parcels"
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
    raise IOError, "File not found %s" % filePath

def WalkParcels(rootParcel):
    repo = rootParcel.itsView
    rootParcelPath = tuple(rootParcel.itsPath)
    rootParcelPathLen = len(rootParcelPath)

    parcels = {}

    parcelKind = repo.findPath("//Schema/Core/Parcel")
    for parcel in KindQuery().run([parcelKind]):
        p = tuple(parcel.itsPath)
        if p[:rootParcelPathLen] == rootParcelPath:
            parcels[p] = parcel

    parcelPaths = parcels.keys()
    parcelPaths.sort()
    for inPathOrder in parcelPaths:
        #print inPathOrder
        yield parcels[inPathOrder]

def LoadParcels(searchPath, repository):
    """
    Load all parcels found along the searchPath (and below)
    """

    Parcel.setupParcels(repository)
    loader = ParcelLoader(repository, LoadDependency, searchPath)

    for directory in string.split(searchPath, os.pathsep):
        for root, dirs, files in os.walk(directory):
            if 'parcel.xml' in files:
                uri = "//parcels/%s" % root[len(directory)+1:]
                uri = uri.replace(os.path.sep, "/")
                parcelFile = os.path.join(root, 'parcel.xml')
                _loadParcel(parcelFile, uri, repository, loader)

    root = repository.findPath("//parcels")
    for parcel in WalkParcels(root):
        parcel.startupParcel()

def LoadParcel(dir, uri, searchPath, repository):
    """
    Load a specific parcel into the supplied uri, and use searchPath to
    find any parcels this one depends on.
    """

    parcelFile = os.path.join(dir, "parcel.xml")
    Parcel.setupParcels(repository)
    loader = ParcelLoader(repository, LoadDependency, searchPath)
    _loadParcel(parcelFile, uri, repository, loader)

    root = repository.findPath("//parcels")
    for parcel in WalkParcels(root):
        parcel.startupParcel()


def _loadParcel(parcelFile, uri, repository, loader):
    """
    Internal method used by LoadParcels and LoadParcel
    """

    parcel = repository.findPath(uri)
    if ((not parcel) or
        (parcel.modifiedOn.ticks() < os.stat(parcelFile).st_mtime)):
        try:
            loader.load(parcelFile, uri)
            if parcel:
                logging.warning("Reloaded the parcel %s" % parcelFile)
                parcel.modifiedOn = DateTime.now()
        except Exception, e:
            logging.exception("Failed to load parcel %s" % parcelFile)
            try:
                repository.cancel()
            except:
                logging.exception("repository.cancel() failed")
                raise RepositoryError, "See log for exceptions"
        else:
            logging.debug("Loaded the parcel %s" % parcelFile)
            repository.commit()
