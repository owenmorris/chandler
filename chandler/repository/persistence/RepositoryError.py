#   Copyright (c) 2004-2006 Open Source Applications Foundation
#
#   Licensed under the Apache License, Version 2.0 (the "License");
#   you may not use this file except in compliance with the License.
#   You may obtain a copy of the License at
#
#       http://www.apache.org/licenses/LICENSE-2.0
#
#   Unless required by applicable law or agreed to in writing, software
#   distributed under the License is distributed on an "AS IS" BASIS,
#   WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
#   See the License for the specific language governing permissions and
#   limitations under the License.


#
# __doc__ strings need to be explicitely set in order not to be removed by -OO
#


class RepositoryError(ValueError):
    __doc__ = "All repository related exceptions go here"


class RepositoryLockNotGrantedError:
    pass

class ExclusiveOpenDeniedError(RepositoryLockNotGrantedError):
    pass

class RepositoryOpenDeniedError(RepositoryLockNotGrantedError):
    pass

class RepositoryPasswordError(RepositoryError):
    pass


class RepositoryOpenError(RepositoryError):
    pass

class RepositoryPlatformError(RepositoryOpenError):
    __doc__ = "Repository was created on %s and cannot be opened on %s"

    def __str__(self):
        return self.__doc__ %(self.args[0], self.args[1])


class RepositoryRunRecoveryError(RepositoryOpenError):
    pass


class RepositoryRestoreError(RepositoryError):
    pass


class VersionConflictError(RepositoryError):
    __doc__ = "Another view changed %s and saved those changes before this view - %s - got a chance to do so. These changes conflict with this thread's changes, the item cannot be saved (0x%0.4x/0x%0.4x)."

    def __str__(self):
        return self.__doc__ %(self.args[0].itsPath, self.args[0].itsView,
                              self.args[1], self.args[2])

    def getItem(self):
        return self.args[0]


class RepositoryVersionError(RepositoryError):
    __doc__ = "%s%s"

    def __str__(self):
        return self.__doc__ %(self.args[0], self.args[1])

class RepositoryFormatVersionError(RepositoryVersionError):
    __doc__ = "Repository format version mismatch, expected version 0x%08x, but got 0x%08x"

class RepositorySchemaVersionError(RepositoryVersionError):
    __doc__ = "Repository core schema version mismatch, expected version 0x%08x, but got 0x%08x"

class RepositoryDatabaseVersionError(RepositoryVersionError):
    __doc__ = "Repository database version mismatch, expected version %s, but got %s"


class NoSuchItemError(RepositoryError):
    __doc__ = "No such item %s, version %d"

    def __str__(self):
        return self.__doc__ % (self.args[0], self.args[1])


class MergeError(VersionConflictError):
    __doc__ = "(%s) merging %s failed because %s, reason code: %s"

    def __str__(self):
        return self.__doc__ %(self.args[0], self.args[1], self.args[2],
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
    KIND   = 6
    CHANGE = 7
    DELETE = 8
    ALIAS  = 9
    
    codeNames = { BUG: 'BUG',
                  RENAME: 'RENAME',
                  MOVE: 'MOVE',
                  NAME: 'NAME',
                  VALUE: 'VALUE',
                  REF: 'REF',
                  KIND: 'KIND',
                  CHANGE: 'CHANGE',
                  DELETE: 'DELETE',
                  ALIAS: 'ALIAS' }


class LoadError(RepositoryError):
    __doc__ = "While loading %s, %s"

    def __str__(self):
        return self.__doc__ %(self.args[0], self.args[1])


class RecursiveLoadItemError(LoadError):
    __doc__ = "Item %s is already being loaded"

    def __str__(self):
        return self.__doc__ %(self.args[0])


class LoadValueError(LoadError):
    __doc__ = "While loading %s.%s, %s"

    def __str__(self):
        return self.__doc__ %(self.args[0], self.args[1], self.args[2])


class SaveError(RepositoryError):
    __doc__ = "While saving %s, %s"

    def __str__(self):
        return self.__doc__ %(self.args[0], self.args[1])


class SaveValueError(RepositoryError):
    __doc__ = "While saving value for '%s' on %s: %s"

    def __str__(self):
        return self.__doc__ %(self.args[1], self.args[0]._repr_(), self.args[2])
