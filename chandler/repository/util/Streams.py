
__revision__  = "$Revision$"
__date__      = "$Date$"
__copyright__ = "Copyright (c) 2003-2004 Open Source Applications Foundation"
__license__   = "http://osafoundation.org/Chandler_0.1_license_terms.htm"

from bz2 import BZ2Compressor, BZ2Decompressor
from zlib import compressobj, decompressobj
from cStringIO import StringIO
from HTMLParser import HTMLParser
from struct import pack, unpack
from PyICU import UnicodeString

from chandlerdb.util.rijndael import Rijndael


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


class BlockOutputStream(object):

    def __init__(self, outputStream, blockSize):

        self.outputStream = outputStream
        self.blockSize = blockSize

        self.remainder = ''
    
    def write(self, data):

        ld = len(data)
        lr = len(self.remainder)
        bs = self.blockSize
        
        if lr > 0 or ld < bs:
            if ld + lr < bs:
                self.remainder += data
                return
            ls = bs - lr
            if ls > 0:
                self.remainder += data[:ls]
                data = data[ls:]
                ld -= ls
            if self.remainder:
                self.writeLen(1)
                self.writeBlocks(self.remainder)
                self.remainder = ''

        lr = ld % bs
        if lr > 0:
            ld -= lr
            self.remainder = data[ld:]
            data = data[:ld]

        max = 0x7fff * bs
        if ld > max:
            i = 0
            while ld > max:
                self.writeLen(0x7fff)
                self.writeBlocks(data[i:i+max])
                ld -= max
                i += max
            if ld > 0:
                data = data[-ld:]
        if ld > 0:
            self.writeLen(ld / bs)
            self.writeBlocks(data)

    def writeLen(self, len):

        self.outputStream.write(pack('>h', len))

    def writeBlocks(self, data):

        self.outputStream.write(data)

    def writePadded(self, data):

        self.outputStream.write(data)

    def flush(self):

        self.outputStream.flush()
        
    def close(self):

        lr = len(self.remainder)
        if lr > 0:
            self.writeLen(-lr)
            self.writePadded(self.remainder)
        self.outputStream.close()


class RijndaelOutputStream(BlockOutputStream):

    def __init__(self, outputStream, key):

        super(RijndaelOutputStream, self).__init__(outputStream, 16)
        self.r = Rijndael()

        if key is None:
            raise ValueError, 'key is None'

        if len(key) == 16:
            keyLen = Rijndael.Key16Bytes
        elif len(key) == 24:
            keyLen = Rijndael.Key24Bytes
        elif len(key) == 32:
            keyLen = Rijndael.Key32Bytes
        else:
            raise ValueError, 'key is not 16, 24 or 32 bytes long'

        self.r.init(Rijndael.ECB, Rijndael.Encrypt, key, keyLen)

    def writeBlocks(self, data):

        super(RijndaelOutputStream, self).writeBlocks(self.r.blockEncrypt(data))

    def writePadded(self, data):

        super(RijndaelOutputStream, self).writePadded(self.r.padEncrypt(data))

    def close(self):

        super(RijndaelOutputStream, self).close()
        del self.r
        

class Base64OutputStream(BlockOutputStream):

    def __init__(self, outputStream):

        super(Base64OutputStream, self).__init__(outputStream, 3)

    def writeBlocks(self, data):

        data = data.encode('base64').replace('\n', '')
        super(Base64OutputStream, self).writeBlocks(data)

    def writePadded(self, data):

        data = data.encode('base64').replace('\n', '')
        super(Base64OutputStream, self).writePadded(data)

    def writeLen(self, len):

        self.outputStream.write(pack('>h', len).encode('base64')[0:3])


class StringOutputStream(object):

    def __init__(self):

        self.output = StringIO()

    def write(self, data):

        self.output.write(data)

    def flush(self):

        self.output.flush()

    def close(self):

        self.output.flush()
        self.string = self.output.getvalue()
        self.output.close()
        

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
        
    def read(self, length=-1):

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


class BlockInputStream(object):

    def __init__(self, inputStream, blockSize):

        self.inputStream = inputStream
        self.blockSize = blockSize

        self.buffer = StringIO()
        self._buffer = StringIO()
        self.rpos = 0
        
    def read(self, length=-1):

        lr = self.buffer.tell() - self.rpos
        if lr > 0:
            if length == lr:
                self.buffer.seek(self.rpos, 0)
                result = self.buffer.read()
                self.buffer.truncate(0)
                self.buffer.reset()
                self.rpos = 0
                return result
            if length > 0 and length < lr:
                self.buffer.seek(self.rpos, 0)
                result = self.buffer.read(length)
                self.rpos += len(result)
                self.buffer.seek(0, 2)
                return result

        while True:
            ld = self.readLen()
            if ld == 0:
                self.buffer.seek(self.rpos, 0)
                result = self.buffer.read()
                self.buffer.truncate(0)
                self.buffer.reset()
                self.rpos = 0
                return result

            if ld < 0:
                self.buffer.write(self.readPadded(self.blockSize))
            elif ld > 0:
                self.buffer.write(self.readBlocks(ld * self.blockSize))

            if length > 0:
                lr = self.buffer.tell() - self.rpos
                if length < lr:
                    self.buffer.seek(self.rpos, 0)
                    result = self.buffer.read(length)
                    self.rpos += len(result)
                    self.buffer.seek(0, 2)
                    return result

    def readBlocks(self, len):

        return self._read(len)

    def readPadded(self, len):

        return self._read(len)

    def readLen(self):

        ls = self._read(2, True)
        if ls == '':
            return 0
        
        return unpack('>h', ls)[0]

    def _read(self, length, eofOk=False):
        
        self._buffer.reset()
        self._buffer.truncate(0)

        while length > 0:
            d = self.inputStream.read(length)
            l = len(d)
            if l == 0:
                if eofOk:
                    return ''
                else:
                    raise ValueError, 'short read'
            if l > length:
                raise ValueError, 'long read'
            self._buffer.write(d)
            length -= l

        return self._buffer.getvalue()

    def close(self):

        self.buffer.close()
        self._buffer.close()
        self.inputStream.close()


class RijndaelInputStream(BlockInputStream):

    def __init__(self, inputStream, key):

        super(RijndaelInputStream, self).__init__(inputStream, 16)
        self.r = Rijndael()

        if key is None:
            raise ValueError, 'key is None'

        if len(key) == 16:
            keyLen = Rijndael.Key16Bytes
        elif len(key) == 24:
            keyLen = Rijndael.Key24Bytes
        elif len(key) == 32:
            keyLen = Rijndael.Key32Bytes
        else:
            raise ValueError, 'key is not 16, 24 or 32 bytes long'

        self.r.init(Rijndael.ECB, Rijndael.Decrypt, key, keyLen)

    def readBlocks(self, len):

        data = super(RijndaelInputStream, self).readBlocks(len)
        return self.r.blockDecrypt(data)
        
    def readPadded(self, len):

        data = super(RijndaelInputStream, self).readPadded(len)
        return self.r.padDecrypt(data)

    def close(self):

        super(RijndaelInputStream, self).close()
        self.r = None


class Base64InputStream(BlockInputStream):

    def __init__(self, inputStream):

        super(Base64InputStream, self).__init__(inputStream, 4)

    def readBlocks(self, len):

        data = super(Base64InputStream, self).readBlocks(len)
        return data.decode('base64')

    def readPadded(self, len):

        data = super(Base64InputStream, self).readPadded(len)
        return data.decode('base64')

    def readLen(self):

        ls = self._read(3, True)
        if ls == '':
            return 0

        return unpack('>h', (ls + '=').decode('base64'))[0]


class StringInputStream(object):

    def __init__(self, string):

        self.input = StringIO(string)

    def read(self, length=-1):

        return self.input.read(length)

    def close(self):

        self.input.close()


class BufferedInputStream(object):

    def __init__(self, sender):

        super(BufferedInputStream, self).__init__()
        self.buffer = StringIO(sender())

    def read(self, length=-1):

        return self.buffer.read(length)

    def close(self):

        self.buffer.close()


class ConcatenatedInputStream(object):

    def __init__(self, *streams):

        self._streams = streams
        self._done = []

    def read(self, length=-1):

        while self._streams:
            data = self._streams[0].read(length)

            if len(data):
                return data
            else:
                self._done.append(self._streams.pop(0))

        return ''

    def close(self):

        for stream in self._streams:
            stream.close()
        for stream in self._done:
            stream.close()

        del self._streams[:]
        del self._done[:]


class NullInputStream(object):

    def read(self, length=-1):
        return ''

    def close(self):
        pass
        

class OutputStreamWriter(object):

    def __init__(self, outputStream, encoding, replace=False):

        super(OutputStreamWriter, self).__init__()

        self.outputStream = outputStream
        self.encoding = encoding or 'utf-8'
        self.mode = replace and 'replace' or 'strict'

    def write(self, text):

        if isinstance(text, unicode):
            text = text.encode(self.encoding, self.mode)

        self.outputStream.write(text)

    def flush(self):

        self.outputStream.flush()

    def close(self):

        self.outputStream.close()


class InputStreamReader(object):

    def __init__(self, inputStream, encoding, replace=False):

        super(InputStreamReader, self).__init__()

        self.inputStream = inputStream
        self.encoding = encoding or 'utf-8'
        self.mode = replace and 'replace' or 'strict'

    def _read(self, length):

        return self.inputStream.read(length)

    def read(self, length=-1):

        text = self._read(length)
        try:
            text = unicode(text, self.encoding, self.mode)
        except LookupError:
            text = unicode(UnicodeString(text, self.encoding, self.mode))

        return text

    def close(self):

        self.inputStream.close()


class StringReader(object):

    def __init__(self, text, encoding=None, replace=False):

        super(StringReader, self).__init__()

        if not isinstance(text, unicode):
            mode = replace and 'replace' or 'strict'
            try:
                self.unicodeText = unicode(text, encoding or 'utf-8', mode)
            except LookupError:
                self.unicodeText = unicode(UnicodeString(text, encoding, mode))

        else:
            self.unicodeText = text

    def read(self, length=-1):

        text = self.unicodeText
        if text is None:
            return ''
        
        if length == -1 or length >= len(text):
            self.unicodeText = None
            return text

        text = text[:length]
        self.unicodeText = self.unicodeText[length:]

        return text

    def close(self):
        pass


class HTMLReader(InputStreamReader):

    def __init__(self, inputStream, encoding, replace=False):

        super(HTMLReader, self).__init__(inputStream, encoding, replace)

        class htmlParser(HTMLParser):

            def __init__(self):

                HTMLParser.__init__(self)

                self.buffer = StringIO()
                self.position = 0

            def handle_data(self, data):

                self.buffer.write(data)

            def _read(self, length):

                buffer = self.buffer
                size = buffer.tell() - self.position

                if length > 0 and size > length:
                    buffer.seek(self.position)
                    data = buffer.read(length)
                    self.position += len(data)
                    buffer.seek(0, 2)

                elif size > 0:
                    buffer.seek(self.position)
                    data = buffer.read(size)
                    self.position = 0
                    buffer.seek(0)

                else:
                    data = ''

                return data
                
        self.parser = htmlParser()

    def _read(self, length):

        while True:
            data = super(HTMLReader, self)._read(length)
            if len(data) > 0:
                self.parser.feed(data)
                data = self.parser._read(length)
                if len(data) == 0:
                    continue
            return data
