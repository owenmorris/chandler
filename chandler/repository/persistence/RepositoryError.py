
__revision__  = "$Revision$"
__date__      = "$Date$"
__copyright__ = "Copyright (c) 2002 Open Source Applications Foundation"
__license__   = "http://osafoundation.org/Chandler_0.1_license_terms.htm"



class RepositoryError(ValueError):
    "All repository related exceptions go here"


class VersionConflictError(RepositoryError):
    "Another thread changed %s and saved those changes before this thread got a chance to do so. These changes conflict with this thread's changes, the item cannot be saved."

    def __str__(self):
        return self.__doc__ %(self.args[0].itsPath)

    def getItem(self):
        return self.args[0]


class NoSuchItemError(RepositoryError):
    "No such item %s, version %d"

    def __str__(self):
        return self.__doc__ % self.args
