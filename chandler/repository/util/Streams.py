
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


class BZ2InputStream(object):

    def __init__(self, inputStream):

        super(BZ2InputStream, self).__init__()

        self.bz2 = BZ2Decompressor()
        self.inputStream = inputStream
        self.extra_data = ''
        
    def read(self, length = -1):

        if len(self.extra_data) > 0:
            data = self.extra_data
            self.extra_data = ''
            
        else:
            while True:
                data = self.inputStream.read(length)
                if len(data) == 0:
                    return ''

                data = self.bz2.decompress(data)
                if len(data) > 0:
                    break
        
            if len(self.bz2.unused_data) > 0:
                buffer = StringIO()
                buffer.write(data)

                while len(self.bz2.unused_data) > 0:
                    bz2 = BZ2Decompressor()
                    buffer.write(bz2.decompress(self.bz2.unused_data))
                    self.bz2 = bz2

                data = buffer.getvalue()
                buffer.close()

        if length > 0 and len(data) > length:
            self.extra_data = data[length:]
            data = data[0:length]

        return data

    def close(self):

        self.inputStream.close()


class ZlibInputStream(object):

    def __init__(self, inputStream):

        super(ZlibInputStream, self).__init__()

        self.zlib = decompressobj()
        self.inputStream = inputStream
        self.extra_data = ''

    def read(self, length = -1):

        if len(self.extra_data) > 0:
            data = self.extra_data
            self.extra_data = ''
            
        else:
            while True:
                data = self.inputStream.read(length)
                if len(data) == 0:
                    return ''
        
                data = self.zlib.decompress(data)
                if len(data) > 0:
                    break
        
            if len(self.zlib.unused_data) > 0:
                buffer = StringIO()
                buffer.write(data)

                while len(self.zlib.unused_data) > 0:
                    zlib = decompressobj()
                    buffer.write(zlib.decompress(self.zlib.unused_data))
                    self.zlib = zlib

                data = buffer.getvalue()
                buffer.close()
            
        if length > 0 and len(data) > length:
            self.extra_data = data[length:]
            data = data[0:length]

        return data

    def close(self):

        self.inputStream.close()


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

