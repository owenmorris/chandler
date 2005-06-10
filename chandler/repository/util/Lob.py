
__revision__  = "$Revision$"
__date__      = "$Date$"
__copyright__ = "Copyright (c) 2003-2004 Open Source Applications Foundation"
__license__   = "http://osafoundation.org/Chandler_0.1_license_terms.htm"

from repository.util.Streams import BZ2OutputStream, BZ2InputStream
from repository.util.Streams import ZlibOutputStream, ZlibInputStream
from repository.util.Streams import RijndaelOutputStream, RijndaelInputStream
from repository.util.Streams import OutputStreamWriter, InputStreamReader
from repository.util.Streams import BufferedOutputStream, BufferedInputStream
from repository.util.Streams import HTMLReader, Base64InputStream


class Lob(object):

    def __init__(self, encoding=None, mimetype='text/plain', indexed=False):

        super(Lob, self).__init__()

        self.encoding = encoding
        self.mimetype = mimetype.lower()
        self._compression = None
        self._encryption = None
        self._key = None                  # not saved in repository
        self._data = ''
        self._append = False
        self._indexed = indexed

    def getOutputStream(self, compression=None, encryption=None, key=None,
                        append=False):

        if compression is None:
            compression = self._compression
        if encryption is None:
            encryption = self._encryption
        if key is None:
            key = self._key

        outputStream = self._getOutputStream(append)

        if encryption:
            if encryption == 'rijndael':
                outputStream = RijndaelOutputStream(outputStream, key)
                self._key = key
            else:
                raise ValueError, '%s encryption not supported' %(encryption)

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

    def getInputStream(self, key=None):

        inputStream = self._getInputStream()
        compression = self._compression
        encryption = self._encryption

        if encryption:
            if encryption == 'rijndael':
                inputStream = RijndaelInputStream(inputStream, key or self._key)
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
        self._version = long(attrs.get('version', '0'))
        self._indexed = attrs.get('indexed', 'False') == 'True'

        if attrs.get('type', 'text') == 'text':
            writer = self.getWriter()
            writer.write(data)
            writer.close()

    def copy(self, view, key=None):

        copy = view._getLobType()(view, self.encoding,
                                  self.mimetype, self._indexed)

        inputStream = self.getInputStream(key)
        outputStream = copy.getOutputStream(self._compression, self._encryption,
                                            key)

        outputStream.write(inputStream.read())
        outputStream.close()
        inputStream.close()

        return copy

    def getWriter(self, compression='bz2', encryption=None, key=None,
                  append=False, replace=False):

        return OutputStreamWriter(self.getOutputStream(compression, encryption,
                                                       key, append),
                                  self.encoding, replace)

    def getReader(self, key=None, replace=False):

        return InputStreamReader(self.getInputStream(key),
                                 self.encoding, replace)

    def getPlainTextReader(self, key=None, replace=False):

        if self.mimetype in Lob._readers:
            return Lob._readers[self.mimetype](self, key, replace)

        return NotImplementedError, "Converting mimetype '%s' to plain text" %(self.mimetype)

    _readers = {
        'text/html': lambda self, key, replace: HTMLReader(self.getInputStream(key), self.encoding, replace), 
        'text/xhtml': lambda self, key, replace: HTMLReader(self.getInputStream(key), self.encoding, replace),
        'text/plain': lambda self, key, replace: self.getReader(key, replace),

        'text/vnd.osaf-stream64': lambda self, key, replace: InputStreamReader(Base64InputStream(self.getInputStream(key)), self.encoding, replace)
    }
