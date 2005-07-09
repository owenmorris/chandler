
__revision__  = "$Revision$"
__date__      = "$Date$"
__copyright__ = "Copyright (c) 2004 Open Source Applications Foundation"
__license__   = "http://osafoundation.org/Chandler_0.1_license_terms.htm"


import threading


class RepositoryError(ValueError):
    "All repository related exceptions go here"


class RepositoryLockNotGrantedError:
    pass

class ExclusiveOpenDeniedError(RepositoryLockNotGrantedError):
    pass

class RepositoryOpenDeniedError(RepositoryLockNotGrantedError):
    pass

class RepositoryPasswordError(RepositoryError):
    pass


class VersionConflictError(RepositoryError):
    "Another view changed %s and saved those changes before this view - %s - got a chance to do so. These changes conflict with this thread's changes, the item cannot be saved (0x%0.4x/0x%0.4x)."

    def __str__(self):
        return self.__doc__ %(self.args[0].itsPath, self.args[0].itsView,
                              self.args[1], self.args[2])

    def getItem(self):
        return self.args[0]


class RepositoryVersionError(RepositoryError):

    def __str__(self):
        return self.__doc__ %(self.args[0], self.args[1])

class RepositoryFormatVersionError(RepositoryVersionError):
    "Repository format version mismatch, expected version 0x%08x, but got 0x%08x"

class RepositorySchemaVersionError(RepositoryVersionError):
    "Repository core schema version mismatch, expected version 0x%08x, but got 0x%08x"


class NoSuchItemError(RepositoryError):
    "No such item %s, version %d"

    def __str__(self):
        return self.__doc__ % (self.args[0], self.args[1])


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
    NAME   = 3
    VALUE  = 4
    REF    = 5
    
    codeNames = { BUG: 'BUG',
                  RENAME: 'RENAME',
                  MOVE: 'MOVE',
                  NAME: 'NAME',
                  VALUE: 'VALUE',
                  REF: 'REF' }


class LoadError(RepositoryError):
    "While loading %s, %s"

    def __str__(self):
        return self.__doc__ %(self.args[0], self.args[1])


class RecursiveLoadItemError(LoadError):
    "Item %s is already being loaded"

    def __str__(self):
        return self.__doc__ %(self.args[0])


class LoadValueError(LoadError):
    "While loading %s.%s, %s"

    def __str__(self):
        return self.__doc__ %(self.args[0], self.args[1], self.args[2])


class SaveError(RepositoryError):
    "While saving %s, %s"

    def __str__(self):
        return self.__doc__ %(self.args[0], self.args[1])


class SaveValueError(RepositoryError):
    "While saving value for '%s' on %s: %s"

    def __str__(self):
        return self.__doc__ %(self.args[1], self.args[0]._repr_(), self.args[2])


class ItemImportError(RepositoryError):
    "While importing %s into %s, %s"

    def __str__(self):
        return self.__doc__ %(self.args[0], self.args[1], self.args[2])


class ImportParentError(ItemImportError):
    "No matching import parent %s for %s found"

    def __str__(self):
        return self.__doc__ %(self.args[0].itsPath, self.args[1]._repr_())

class ImportKindError(ItemImportError):
    "No matching import kind %s for %s found"

    def __str__(self):
        return self.__doc__ %(self.args[0].itsPath, self.args[1]._repr_())
