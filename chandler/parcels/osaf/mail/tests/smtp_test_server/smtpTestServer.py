#!/usr/bin/python
from twisted.internet.protocol import Protocol, Factory
from twisted.internet import reactor

PORT = 2500

### Protocol Implementation

# This is just about the simplest possible protocol
class SMTPTestServer(Protocol):
    def dataReceived(self, data):
        """As soon as any data is received, write it back."""
        self.transport.write(data)


def main():

    f = Factory()
    f.protocol = SMTPTestServer
    reactor.listenTCP(PORT, f)
    reactor.run()

if __name__ == '__main__':
    main()
