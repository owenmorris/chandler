from application import Globals
from osaf.framework.blocks.ContainerBlocks import BoxContainer
from repository.parcel.Parcel import Parcel
from M2Crypto import SSL, Rand, threading as m2threading
import thread
from socket import *
import seedm2
import logging
# XXX
import server
import client3
from PyEGADS import egads

class PKITestViewParcel(Parcel):

    def __init__(self, name, parent, kind):
        super (PKITestViewParcel, self).__init__ (name, parent, kind)
        # XXX __init__ does not seem to run
        #m2threading.init()
        #self.seeder = seedm2.Seeder()
        #self.seeder.start()

    def __del__(self):
        Parcel.__del__(self)        
        # XXX Is there a way to kill self.seeder if it is alive?
        # XXX __del__ does not seem to run
        Rand.save_file('randpool.dat')
        m2threading.cleanup()

    def startupParcel(self):
        # XXX This should probably be in the __init__ method
        #log = logging.getLogger()
        #log.debug('pkitest starting to load parcel')
        m2threading.init()
        #self.seeder = seedm2.Seeder()
        #self.seeder.start()

        # Make sure our view is in the sidebar
        Parcel.startupParcel(self)
        rep = self.getRepository()
        urlRoot = rep.findPath("//parcels/osaf/views/main/URLRoot")
        pkiNode = rep.findPath("//parcels/pkitest/views/PKITestViewNode")
        if urlRoot and pkiNode:
            urlRoot.children.append(pkiNode)

class PKITestView(BoxContainer):

    def OnStartStopServerEvent(self, notification):
        log = logging.getLogger('m2seeder')
        log.setLevel(logging.INFO)
        log.info('Start/Stop server called')
        
        serverPort = Globals.repository.findPath('//parcels/pkitest/views/PKITestView/ServerPortText')
        sPort = serverPort.widget.GetValue()
   
        ctx = server.setup_server_ctx()
        sock = socket(AF_INET, SOCK_STREAM)
        sock.setsockopt(SOL_SOCKET, SO_REUSEADDR, 1)
        sock.bind(('', int(sPort)))
        sock.listen(5)
        conn, addr = sock.accept()

        log.info('accepted: ' + str(conn) + str(addr))
        
        self.server = server.Server()
        self.server.ctx = ctx
        self.server.sock = conn
        self.server.addr = addr
        self.server.start()

    def OnConnectDisconnectClientEvent(self, notification):
        ctx = setup_client_ctx()
        conn = SSL.Connection(ctx)
        if conn.connect(('127.0.0.1', 9999)) < 0:
            print "***Connection error"
        post_connection_check(conn)

        #if do_client_loop(conn):
        #    conn.close()
        #else:
        #    conn.clear()
  
    def OnSendDataToServerEvent(self, notification):
        pass
