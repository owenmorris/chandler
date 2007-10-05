#   Copyright (c) 2004-2007 Open Source Applications Foundation
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

from struct import pack, unpack
from time import time

from chandlerdb.util.c import UUID, allocateBuffer
from chandlerdb.persistence.c import DBLockDeadlockError, DBInvalidArgError

from repository.persistence.DBContainer import DBContainer
from repository.persistence.RepositoryError import RepositoryError


class FileContainer(DBContainer):

    BLOCK_SHIFT = 14
    BLOCK_LEN = 1 << BLOCK_SHIFT
    BLOCK_MASK = BLOCK_LEN - 1

    def __init__(self, store):

        self._blocks = None
        super(FileContainer, self).__init__(store)

    def open(self, name, txn, **kwds):

        super(FileContainer, self).open(name, txn, dbname = 'files', **kwds)

        self._blocks = self.openDB(txn, name, 'blocks',
                                   kwds.get('ramdb', False),
                                   kwds.get('create', False),
                                   False)

    def close(self):

        if self._blocks is not None:
            self._blocks.close()
            self._blocks = None

        super(FileContainer, self).close()

    def compact(self, txn=None):

        super(FileContainer, self).compact(txn)
        self._compact(txn, self._blocks)

    def createFile(self, name):

        return OutputStream(self, name, True)

    def appendFile(self, name):

        return OutputStream(self, name, False)

    def deleteFile(self, name):

        return File(self, name).delete()

    def fileExists(self, name):

        return File(self, name).exists()

    def fileLength(self, name):

        file = File(self, name)

        if file.exists():
            return file.getLength()

        raise RepositoryError, "File does not exist: %s" %(name)
    
    def fileModified(self, name):

        file = File(self, name)

        if file.exists():
            return file.getTimeModified()

        raise RepositoryError, "File does not exist: %s" %(name)

    def list(self):

        cursor = None
        results = []

        while True:
            try:
                cursor = self.c.openCursor()
                value = cursor.first(self.c.flags, None)

                while value is not None:
                    value = value[0]
                    length = unpack('>H', value[0:2])[0]
                    results.append(value[2:2+length])

                    while True:
                        try:
                            value = cursor.next(self.c.flags, None)
                            break
                        except DBLockDeadlockError:
                            self.store._logDL()
                        
                return results

            finally:
                self.c.closeCursor(cursor)

    def openFile(self, name):

        return InputStream(self, name)

    def renameFile(self, old, new):

        File(self, old).rename(new)

    def touchFile(self, name):

        file = File(self, name)
        length = 0
        
        if file.exists():
            length = file.getLength()

        file.modify(length, long(time() * 1000))


class LOBContainer(FileContainer):

    def purgeLob(self, txn, counter, uLob, toVersion=None):
    
        count = self.deleteFile(uLob._uuid)
        self.delete(uLob._uuid, txn)

        counter.fileCount += 1
        counter.blockCount += count


class File(object):

    def __init__(self, container, name, create=False, value=None):

        super(File, self).__init__()

        self._container = container
        self.setName(name)

        if not self.exists():
            self._uuid = UUID()
            self.length = 0
            
        elif create:
            self.length = 0

    def getName(self):

        return self.name

    def setName(self, name):

        if isinstance(name, unicode):
            name = name.encode('utf-8')

        self._key = "%s%s" %(pack('>H', len(name)), name)
        self.name = name

    def getKey(self):

        try:
            return self._uuid
        except AttributeError:
            raise RepositoryError, "Uninitialized file"

    def getLength(self):

        return self.length

    def getTimeModified(self):

        try:
            return self.timeModified
        except AttributeError:
            raise RepositoryError, "Uninitialized file"

    def exists(self):

        value = self._container.get(self._key)
        if value is None:
            return False
        
        zero, self.length, self.timeModified, uuid = unpack('>LLQ16s', value)
        self._uuid = UUID(uuid)

        return True

    def modify(self, length, timeModified):

        data = pack('>LLQ16s', 0L, length, timeModified, self.getKey()._uuid)
        self._container.put(self._key, data)
        
        self.length = length
        self.timeModified = timeModified

    def delete(self):

        count = 0
        cursor = None
        container = self._container
        blocks = container._blocks
        
        try:
            cursor = container.c.openCursor(blocks)
            key = self.getKey()._uuid
            
            value = cursor.set_range(key, container.c.flags, None)
            while value is not None and value[0].startswith(key):
                cursor.delete()
                count += 1
                value = cursor.next(container.c.flags, None)

            container.delete(self._key)

        finally:
            container.c.closeCursor(cursor, blocks)

        return count

    def rename(self, name):

        if not self.exists():
            raise RepositoryError, "File does not exist: %s" %(self.getName())

        newFile = File(self._container, name)

        if newFile.exists():
            newFile.delete()

        data = self._container.get(self._key)
        self._container.delete(self._key)
        self.setName(name)
        self._container.put(self._key, data)


class Block(object):

    def __init__(self, container, file):

        super(Block, self).__init__()

        self._container = container
        self._key = pack('>16sll', file.getKey()._uuid, 0L, 0L)
        self._data = None
        self._position = 0
        self._len = 0

    def getKey(self):

        return self._key

    def getData(self):

        return self._data

    def seek(self, position, write=False):

        position = int(position)
        key = pack('>16sll', self._key[0:16], 0,
                   position >> self._container.BLOCK_SHIFT)

        if self._data is None or key != self._key:
            self._key = key
            container = self._container
            data = container.get(self._key, container._blocks)

            if data is not None:
                self._len = len(data)
                if write:
                    self._data = allocateBuffer(self._container.BLOCK_LEN)
                    self._data[0:self._len] = data
                else:
                    self._data = buffer(data)
            else:
                self._data = allocateBuffer(self._container.BLOCK_LEN)

        self._position = position & self._container.BLOCK_MASK

    def put(self):

        if self._data is not None:
            container = self._container
            data = self._data[0:self._len]
            self._data = None
            container.put(self._key, data, container._blocks)

    def write(self, data):

        size = len(data)
        self._data[self._position:self._position+size] = data
        self._position += size
        self._len = max(self._len, self._position)

    def read(self, size):

        data = self._data[self._position:self._position+size]
        self._position += size

        return data


class OutputStream(object):

    def __init__(self, container, name, create=False):

        super(OutputStream, self).__init__()

        self._container = container
        self._file = File(container, name, create)
        self._block = Block(container, self._file)
        self.length = self._file.getLength()
        self.position = 0

        self.seek(self.length);

    def close(self):

        if self.length > 0:
            self._block.put()

        self._file.modify(self.length, long(time() * 1000))

    def write(self, buffer, length=-1):

        blockPos = self.position & self._container.BLOCK_MASK
        offset = 0
        if length < 0:
            length = len(buffer)

        while blockPos + length >= self._container.BLOCK_LEN:
            blockLen = self._container.BLOCK_LEN - blockPos

            self._block.write(buffer[offset:offset+blockLen])
            self._block.put()

            length -= blockLen
            offset += blockLen
            self.position += blockLen
            
            self._block.seek(self.position, True)
            blockPos = 0

        if length > 0:
            if offset == 0 and length == len(buffer):
                self._block.write(buffer)
            else:
                self._block.write(buffer[offset:offset+length])
            self.position += length

        if self.position > self.length:
            self.length = self.position

    def seek(self, pos):

        if pos > self.length:
            raise RepositoryError, "Seeking past end of file"

        if ((pos >> self._container.BLOCK_SHIFT) !=
            (self.position >> self._container.BLOCK_SHIFT)):
            self._block.put()

        self._block.seek(pos, True)
        self.position = pos

    def flush(self):
        pass


class InputStream(object):

    def __init__(self, container, name):

        super(InputStream, self).__init__()

        self._container = container
        self._file = File(container, name)

        if not self._file.exists():
            raise RepositoryError, "File does not exist: %s" %(name)

        self.length = self._file.getLength()
        self._block = Block(container, self._file)

        self.seek(0L)

    def clone(self):

        clone = type(self)(self._container, self._file.getName())
        clone.seek(self.position)
        return clone
        
    def close(self):
        pass

    def read(self, length=-1):

        blockPos = self.position & self._container.BLOCK_MASK
        offset = 0

        if length < 0:
            length = self.length - self.position

        if self.position + length > self.length:
            length = self.length - self.position

        if not length:
            return ''

        buffer = allocateBuffer(int(length))

        while blockPos + length >= self._container.BLOCK_LEN:
            blockLen = self._container.BLOCK_LEN - blockPos

            data = self._block.read(blockLen)
            buffer[offset:offset+blockLen] = data

            length -= blockLen
            offset += blockLen
            self.position += blockLen

            self._block.seek(self.position)
            blockPos = 0

        if length > 0:
            buffer[offset:offset+length] = self._block.read(length)
            self.position += length
            offset += length

        return buffer[0:offset]

    def seek(self, pos):

        if pos > self.length:
            raise RepositoryError, "seeking past end of file"

        self._block.seek(pos)
        self.position = pos
