
__revision__  = "$Revision$"
__date__      = "$Date$"
__copyright__ = "Copyright (c) 2002 Open Source Applications Foundation"
__license__   = "http://osafoundation.org/Chandler_0.1_license_terms.htm"

from bz2 import BZ2Compressor, BZ2Decompressor
from cStringIO import StringIO


class BZ2OutputStream(BZ2Compressor):

    def __init__(self, outputStream, level=9):

        super(BZ2OutputStream, self).__init__(level)
        self.outputStream = outputStream

    def write(self, data):

        self.outputStream.write(self.compress(data))

    def flush(self):

        self.outputStream.write(super(BZ2OutputStream, self).flush())
        self.outputStream.flush()

    def close(self):

        self.flush()
        self.outputStream.close()


class BufferedOutputStream(object):

    def __init__(self, receiver):

        super(BufferedOutputStream, self).__init__()

        self.buffer = StringIO()
        self.receiver = receiver

    def write(self, data):

        self.buffer.write(data)

    def flush(self):

        self.buffer.flush()

    def close(self):

        self.receiver(self.buffer.getvalue())
        self.buffer.close()


class BZ2InputStream(BZ2Decompressor):

    def __init__(self, inputStream):

        super(BZ2InputStream, self).__init__()
        self.inputStream = inputStream

    def read(self):

        return self.decompress(self.inputStream.read())

    def close(self):

        self.inputStream.close()


class BufferedInputStream(object):

    def __init__(self, sender):

        super(BufferedInputStream, self).__init__()
        self.buffer = StringIO(sender())

    def read(self):

        return self.buffer.read()

    def close(self):

        self.buffer.close()


class OutputStreamWriter(object):

    def __init__(self, outputStream, encoding):

        super(OutputStreamWriter, self).__init__()
        self.outputStream = outputStream
        self.encoding = encoding

    def write(self, text):

        if isinstance(text, unicode):
            text = text.encode(self.encoding)

        self.outputStream.write(text)

    def flush(self):

        self.outputStream.flush()

    def close(self):

        self.outputStream.close()


class InputStreamReader(object):

    def __init__(self, inputStream, encoding):

        super(InputStreamReader, self).__init__()
        self.inputStream = inputStream
        self.encoding = encoding

    def read(self):

        text = self.inputStream.read()
        text = unicode(text, self.encoding)

        return text

    def close(self):

        self.inputStream.close()

