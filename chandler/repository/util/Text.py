
__revision__  = "$Revision$"
__date__      = "$Date$"
__copyright__ = "Copyright (c) 2002 Open Source Applications Foundation"
__license__   = "http://osafoundation.org/Chandler_0.1_license_terms.htm"

from repository.util.Streams import BZ2OutputStream, BZ2InputStream
from repository.util.Streams import OutputStreamWriter, InputStreamReader
from repository.util.Streams import BufferedOutputStream, BufferedInputStream


class Text(object):

    def __init__(self, encoding='utf-8', mimetype='text/plain'):

        super(Text, self).__init__()
        
        self.encoding = encoding
        self.mimetype = mimetype
        self._compression = None
        self._data = ''
        
    def getWriter(self, compression='bz2'):

        outputStream = self._getBufferedOutputStream()
        if compression == 'bz2':
            outputStream = BZ2OutputStream(outputStream)
            self._compression = compression

        return OutputStreamWriter(outputStream, self.encoding)

    def getReader(self):

        inputStream = self._getBufferedInputStream()
        if self._compression == 'bz2':
            inputStream = BZ2InputStream(inputStream)

        return InputStreamReader(inputStream, self.encoding)

    def _getBufferedOutputStream(self):

        return BufferedOutputStream(lambda data: self._setData(data))

    def _getBufferedInputStream(self):

        return BufferedInputStream(lambda: self._getData())

    def _setData(self, data):

        self._data = data

    def _getData(self):

        return self._data
