
__revision__  = "$Revision$"
__date__      = "$Date$"
__copyright__ = "Copyright (c) 2002 Open Source Applications Foundation"
__license__   = "http://osafoundation.org/Chandler_0.1_license_terms.htm"

from bz2 import BZ2Compressor, BZ2Decompressor
from zlib import compressobj, decompressobj
from cStringIO import StringIO


class BZ2OutputStream(BZ2Compressor):

    def __init__(self, outputStream, level=9):

        super(BZ2OutputStream, self).__init__(level)
        self.outputStream = outputStream

    def write(self, data):

        if data:
            self.outputStream.write(self.compress(data))

    def flush(self):

        self.outputStream.write(super(BZ2OutputStream, self).flush())
        self.outputStream.flush()

    def close(self):

        self.flush()
        self.outputStream.close()


class ZlibOutputStream(object):

    def __init__(self, outputStream, level=9):

        super(ZlibOutputStream, self).__init__(level)
        self.compressobj = compressobj(level)
        self.outputStream = outputStream

    def write(self, data):

        if data:
            self.outputStream.write(self.compressobj.compress(data))

    def flush(self):

        self.outputStream.write(self.compressobj.flush())
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


class CompressedInputStream(object):

    def __init__(self, inputStream):

        super(CompressedInputStream, self).__init__()

        self.decompressor = self._decompressor()
        self.inputStream = inputStream
        self.extra_data = None

    def _decompressor(self):

        raise NotImplementedError, "CompressedInputStream._decompressor"
        
    def read(self, length = -1):

        if self.extra_data is not None:
            data = self.extra_data.read(length)
            if len(data) > 0:
                return data

            self.extra_data.close()
            self.extra_data = None
            
        data = ''
        while len(data) == 0:
            unused_data = ''
            while len(data) == 0 and len(unused_data) == 0:
                raw = self.inputStream.read(length)
                if len(raw) == 0:
                    return ''

                try:
                    data = self.decompressor.decompress(raw)
                except EOFError:   # only way to find out
                    self.decompressor = self._decompressor()
                    data = self.decompressor.decompress(raw)

                unused_data = self.decompressor.unused_data
        
            if len(unused_data) > 0:
                buffer = StringIO()
                buffer.write(data)

                while len(unused_data) > 0:
                    self.decompressor = self._decompressor()
                    buffer.write(self.decompressor.decompress(unused_data))
                    unused_data = self.decompressor.unused_data

                data = buffer.getvalue()
                buffer.close()

        if length > 0 and len(data) > length:
            self.extra_data = StringIO(data)
            data = self.extra_data.read(length)

        return data

    def close(self):

        self.inputStream.close()


class BZ2InputStream(CompressedInputStream):

    def _decompressor(self):

        return BZ2Decompressor()


class ZlibInputStream(CompressedInputStream):

    def _decompressor(self):

        return decompressobj()


class BufferedInputStream(object):

    def __init__(self, sender):

        super(BufferedInputStream, self).__init__()
        self.buffer = StringIO(sender())

    def read(self, length = -1):

        return self.buffer.read(length)

    def close(self):

        self.buffer.close()


class ConcatenatedInputStream(object):

    def __init__(self, *streams):

        self._streams = streams
        self._done = []

    def read(self, length = -1):

        while self._streams:
            data = self._streams[0].read(length)

            if len(data):
                return data
            else:
                self._done.append(self._streams.pop(0))

    def close(self):

        for stream in self._streams:
            stream.close()
        for stream in self._done:
            stream.close()

        del self._streams[:]
        del self._done[:]


class NullInputStream(object):

    def read(self, length = -1):
        return ''

    def close(self):
        pass
        

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

    def read(self, length = -1):

        text = self.inputStream.read(length)
        text = unicode(text, self.encoding)

        return text

    def close(self):

        self.inputStream.close()

