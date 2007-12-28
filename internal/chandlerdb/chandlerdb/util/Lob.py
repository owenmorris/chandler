#   Copyright (c) 2003-2007 Open Source Applications Foundation
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


from chandlerdb.item import Indexable
from chandlerdb.util.Streams import BZ2OutputStream, BZ2InputStream
from chandlerdb.util.Streams import ZlibOutputStream, ZlibInputStream
from chandlerdb.util.Streams import RijndaelOutputStream, RijndaelInputStream
from chandlerdb.util.Streams import OutputStreamWriter, InputStreamReader
from chandlerdb.util.Streams import BufferedOutputStream, BufferedInputStream
from chandlerdb.util.Streams import HTMLReader, Base64InputStream


class Lob(Indexable):

    def __init__(self, encoding=None, mimetype='text/plain', indexed=None):

        self.encoding = encoding
        self.mimetype = mimetype.lower()
        self._compression = None
        self._encryption = None
        self._key = None                  # not saved in repository
        self._iv = None                   # saved in repository
        self._data = ''
        self._append = False
        self._indexed = indexed

    def isIndexed(self):

        return self._indexed

    def getOutputStream(self, compression=None,
                        encryption=None, key=None, iv=None,
                        append=False):

        if compression is None:
            compression = self._compression
        if encryption is None:
            encryption = self._encryption
        if key is None:
            key = self._key
        if iv is None:
            iv = self._iv

        outputStream = self._getOutputStream(append)

        if encryption:
            if encryption == 'rijndael':
                outputStream = RijndaelOutputStream(outputStream, key, iv)
                self._key = key
                self._iv = outputStream.getIV()
            else:
                raise ValueError, '%s encryption not supported' %(encryption)
        else:
            self._iv = None

        if compression:
            if compression == 'bz2':
                outputStream = BZ2OutputStream(outputStream)
            elif compression == 'zlib':
                outputStream = ZlibOutputStream(outputStream)
            else:
                raise ValueError, '%s compression not supported' %(compression)

        self._encryption = encryption
        self._compression = compression

        return outputStream

    def getInputStream(self, key=None, iv=None):

        inputStream = self._getInputStream()
        compression = self._compression
        encryption = self._encryption

        if encryption:
            if encryption == 'rijndael':
                inputStream = RijndaelInputStream(inputStream,
                                                  key or self._key,
                                                  iv or self._iv)
            else:
                raise ValueError, '%s encryption not supported' %(encryption)

        if compression:
            if compression == 'bz2':
                inputStream = BZ2InputStream(inputStream)
            elif compression == 'zlib':
                inputStream = ZlibInputStream(inputStream)
            else:
                raise ValueError, '%s compression not supported' %(compression)

        return inputStream

    def _getOutputStream(self, append):

        self._append = append
        return BufferedOutputStream(lambda data: self._setData(data))

    def _getInputStream(self):

        return BufferedInputStream(lambda: self._getData())

    def _setData(self, data):

        self._data = data

    def _getData(self):

        return self._data

    def load(self, data, attrs):
        
        self.mimetype = attrs.get('mimetype', 'text/plain')
        if attrs.has_key('encoding'):
            self.encoding = attrs['encoding']

        self._compression = attrs.get('compression', None)
        self._encryption = attrs.get('encryption', None)
        self._iv = attrs.get('iv', '').decode('hex') or None
        self._version = long(attrs.get('version', '0'))

        indexed = attrs.get('indexed', None)
        if indexed is not None:
            self._indexed = indexed == 'True'
        else:
            self._indexed = None

        if attrs.get('type', 'text') == 'text':
            writer = self.getWriter()
            writer.write(data)
            writer.close()

    def copy(self, view, key=None, iv=None):

        copy = view._getLobType()(view, self.encoding,
                                  self.mimetype, self._indexed)

        inputStream = self.getInputStream(key)
        outputStream = copy.getOutputStream(self._compression, self._encryption,
                                            key, iv)

        outputStream.write(inputStream.read())
        outputStream.close()
        inputStream.close()

        return copy

    def getWriter(self, compression='bz2', encryption=None, key=None, iv=None,
                  append=False, replace=False):

        return OutputStreamWriter(self.getOutputStream(compression, encryption,
                                                       key, iv, append),
                                  self.encoding, replace)

    def getReader(self, key=None, iv=None, replace=False):

        return InputStreamReader(self.getInputStream(key, iv),
                                 self.encoding, replace)

    def getPlainTextReader(self, key=None, iv=None, replace=False):

        if self.mimetype in Lob._readers:
            return Lob._readers[self.mimetype](self, key, iv, replace)

        return NotImplementedError, "Converting mimetype '%s' to plain text" %(self.mimetype)

    _readers = {
        'text/html': lambda self, key, iv, replace: HTMLReader(self.getInputStream(key, iv), self.encoding, replace), 
        'text/xhtml': lambda self, key, iv, replace: HTMLReader(self.getInputStream(key, iv), self.encoding, replace),
        'text/plain': lambda self, key, iv, replace: self.getReader(key, iv, replace),
        'text/vnd.osaf-stream64': lambda self, key, iv, replace: InputStreamReader(Base64InputStream(self.getInputStream(key, iv)), self.encoding, replace)
    }
