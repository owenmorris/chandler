from application import Globals
from OSAF.framework.blocks.ContainerBlocks import BoxContainer
from repository.parcel.Parcel import Parcel
from M2Crypto import SSL, Rand, threading
from PyEGADS import egads
import thread
from socket import *
# XXX
import server3
import client3

class PKITestViewParcel(Parcel):

    def __init__(self, name, parent, kind):
        Parcel.__init__(self, name, parent, kind)

    def startupParcel(self):
        # Make sure our view is in the sidebar
        Parcel.startupParcel(self)
        rep = self.getRepository()
        urlRoot = rep.find("//parcels/OSAF/views/main/URLRoot")
        pkiNode = rep.find("//parcels/pkitest/views/PKITestViewNode")
        if urlRoot and pkiNode:
            urlRoot.children.append(pkiNode)

class PKITestView(BoxContainer):

    def OnStartStopServerEvent(self, notification):
        serverPort = Globals.repository.find('//parcels/pkitest/views/PKITestView/ServerPortText')
        wxServerPortText = Globals.association[serverPort.getUUID( )]
        sPort = wxServerPortText.GetValue()
   
        threading.init()
        Rand.load_file('randpool.dat', -1) 
        ctx = server3.setup_server_ctx()
        sock = socket(AF_INET, SOCK_STREAM)
        sock.setsockopt(SOL_SOCKET, SO_REUSEADDR, 1)
        sock.bind(('', int(sPort)))
        sock.listen(5)
        while 1:
            conn, addr = sock.accept()
            thread.start_new_thread(server3.server_thread, (ctx, conn, addr))
        Rand.save_file('randpool.dat')
        threading.cleanup()

    def OnConnectDisconnectClientEvent(self, notification):
        pass

    def OnSendDataToServerEvent(self, notification):
        pass
