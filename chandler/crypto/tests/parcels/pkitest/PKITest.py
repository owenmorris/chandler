from OSAF.framework.blocks.ContainerBlocks import BoxContainer
from repository.parcel.Parcel import Parcel
from M2Crypto import SSL

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

    def OnStartStoppServerEvent(self, notification):
        pass

    def OnConnectDisconnectClientEvent(self, notification):
        pass

    def OnSendDataToServerEvent(self, notification):
        pass
