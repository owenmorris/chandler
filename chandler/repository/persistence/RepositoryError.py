
__revision__  = "$Revision$"
__date__      = "$Date$"
__copyright__ = "Copyright (c) 2002 Open Source Applications Foundation"
__license__   = "http://osafoundation.org/Chandler_0.1_license_terms.htm"



class RepositoryError(ValueError):
    "All repository related exceptions go here"


class VersionConflictError(RepositoryError):
    "Another view changed %s and saved those changes before this view - %s - got a chance to do so. These changes conflict with this thread's changes, the item cannot be saved (0x%0.4x/0x%0.4x)."

    def __str__(self):
        return self.__doc__ %(self.args[0].itsPath, self.args[0].itsView,
                              self.args[1], self.args[2])

    def getItem(self):
        return self.args[0]


class NoSuchItemError(RepositoryError):
    "No such item %s, version %d"

    def __str__(self):
        return self.__doc__ % self.args


class MergeError(VersionConflictError):
    "(%s) merging %s failed because %s, reason code: %s"

    def __str__(self):
        return self.__doc__ %(self.args[0], self.args[1].itsPath, self.args[2],
                              self.getReasonCodeName())

    def getReasonCode(self):
        return self.args[3]

    def getReasonCodeName(self):
        return MergeError.codeNames.get(self.args[3], str(self.args[3]))

    def getItem(self):
        return self.args[1]

    BUG    = 0
    RENAME = 1
    MOVE   = 2

    codeNames = { BUG: 'BUG', RENAME: 'RENAME', 'MOVE': MOVE }
