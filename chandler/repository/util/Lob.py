
__revision__  = "$Revision$"
__date__      = "$Date$"
__copyright__ = "Copyright (c) 2003-2004 Open Source Applications Foundation"
__license__   = "http://osafoundation.org/Chandler_0.1_license_terms.htm"

from repository.util.Streams import BZ2OutputStream, BZ2InputStream
from repository.util.Streams import ZlibOutputStream, ZlibInputStream
from repository.util.Streams import OutputStreamWriter, InputStreamReader
from repository.util.Streams import BufferedOutputStream, BufferedInputStream
from repository.util.Streams import HTMLReader


class Lob(object):

    def __init__(self, mimetype='text/plain', indexed=False):

        super(Lob, self).__init__()

        self.mimetype = mimetype.lower()
        self._compression = None
        self._data = ''
        self._append = False
        self._indexed = indexed

    def getOutputStream(self, compression=None, append=False):

        outputStream = self._getOutputStream(append)

        if compression:
            if compression == 'bz2':
                outputStream = BZ2OutputStream(outputStream)
            elif compression == 'zlib':
                outputStream = ZlibOutputStream(outputStream)
            else:
                raise ValueError, '%s compression not supported' %(compression)

        self._compression = compression

        return outputStream

    def getInputStream(self):

        inputStream = self._getInputStream()
        compression = self._compression

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


class Text(Lob):

    def __init__(self, encoding='utf-8', mimetype='text/plain', indexed=False):

        super(Text, self).__init__(mimetype, indexed)
        self.encoding = encoding
        
    def getWriter(self, compression='bz2', append=False):

        return OutputStreamWriter(self.getOutputStream(compression, append),
                                  self.encoding)

    def getReader(self):

        return InputStreamReader(self.getInputStream(), self.encoding)

    def getPlainTextReader(self):

        if self.mimetype in Text._readers:
            return Text._readers[self.mimetype](self)

        return NotImplementedError, "Converting mimetype '%s' to plain text" %(self.mimetype)

    _readers = {
        'text/html': lambda self: HTMLReader(self.getInputStream(),
                                             self.encoding), 
        'text/xhtml': lambda self: HTMLReader(self.getInputStream(),
                                              self.encoding),
        'text/plain': lambda self: self.getReader()
    }


class Binary(Lob):

    def __init__(self, mimetype='application/binary', indexed=False):

        super(Binary, self).__init__(mimetype, indexed)

    def getPlainTextReader(self):

        if self.mimetype in Binary._readers:
            return Binary._readers[self.mimetype](self)

        return NotImplementedError, "Converting mimetype '%s' to plain text" %(self.mimetype)

    _readers = {}
