
__revision__  = "$Revision$"
__date__      = "$Date$"
__copyright__ = "Copyright (c) 2002 Open Source Applications Foundation"
__license__   = "http://osafoundation.org/Chandler_0.1_license_terms.htm"

from repository.util.Streams import BZ2OutputStream, BZ2InputStream
from repository.util.Streams import ZlibOutputStream, ZlibInputStream
from repository.util.Streams import OutputStreamWriter, InputStreamReader
from repository.util.Streams import BufferedOutputStream, BufferedInputStream


class Lob(object):

    def __init__(self, mimetype='text/plain'):

        super(Lob, self).__init__()

        self.mimetype = mimetype
        self._compression = None
        self._data = ''

    def getOutputStream(self, compression=None):

        outputStream = self._getBufferedOutputStream()

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

        inputStream = self._getBufferedInputStream()
        compression = self._compression

        if compression:
            if compression == 'bz2':
                inputStream = BZ2InputStream(inputStream)
            elif compression == 'zlib':
                inputStream = ZlibInputStream(inputStream)
            else:
                raise ValueError, '%s compression not supported' %(compression)

        return inputStream

    def _getBufferedOutputStream(self):

        return BufferedOutputStream(lambda data: self._setData(data))

    def _getBufferedInputStream(self):

        return BufferedInputStream(lambda: self._getData())

    def _setData(self, data):

        self._data = data

    def _getData(self):

        return self._data


class Text(Lob):

    def __init__(self, encoding='utf-8', mimetype='text/plain'):

        super(Text, self).__init__(mimetype)
        
        self.encoding = encoding
        
    def getWriter(self, compression='bz2'):

        return OutputStreamWriter(self.getOutputStream(compression),
                                  self.encoding)

    def getReader(self):

        return InputStreamReader(self.getInputStream(), self.encoding)


class Binary(Lob):

    def __init__(self, mimetype='text/plain'):

        super(Binary, self).__init__(mimetype)
