
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

    def getWriter(self, compression='bz2', encryption=None, key=None,
                  append=False):

        return OutputStreamWriter(self.getOutputStream(compression, encryption,
                                                       key, append),
                                  self.encoding)

    def getReader(self, key=None):

        return InputStreamReader(self.getInputStream(key), self.encoding)

    def getPlainTextReader(self, key=None):

        if self.mimetype in Lob._readers:
            return Lob._readers[self.mimetype](self, key)

        return NotImplementedError, "Converting mimetype '%s' to plain text" %(self.mimetype)

    _readers = {
        'text/html': lambda self, key: HTMLReader(self.getInputStream(key),
                                                  self.encoding), 
        'text/xhtml': lambda self, key: HTMLReader(self.getInputStream(key),
                                                   self.encoding),
        'text/plain': lambda self, key: self.getReader(key),

        'text/vnd.osaf-stream64': lambda self, key: InputStreamReader(Base64InputStream(self.getInputStream(key)), self.encoding)
    }
