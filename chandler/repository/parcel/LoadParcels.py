""" Parcel loading"""

__revision__  = "$Revision$"
__date__      = "$Date$"
__copyright__ = "Copyright (c) 2003 Open Source Applications Foundation"
__license__   = "http://osafoundation.org/Chandler_0.1_license_terms.htm"

import os, string, logging

from repository.schema.ParcelLoader import ParcelLoader
from repository.schema.Parcel import Parcel

def LoadDependency(repository, uri, searchPath):
    # Easy success if we find the parcel
    parcel = repository.find(uri)
    if parcel: return

    # Look for the parcel anywhere on the path
    file = FindParcelFile(uri, searchPath)
    loader = ParcelLoader(repository, LoadDependency, searchPath)
    loader.load(file, uri)

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
                if not parcel:
                    try:
                        path = os.path.join(root, 'parcel.xml')
                        loader.load(path, uri)
                    except:
                        repository.cancel()
                        logging.exception("Failed to load parcel %s" % path)
                    else:
                        repository.commit()

    root = repository.find("//Parcels")
    for parcel in WalkParcels(root):
        parcel.startupParcel()
