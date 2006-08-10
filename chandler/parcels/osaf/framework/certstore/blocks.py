#   Copyright (c) 2005-2006 Open Source Applications Foundation
#
#   Licensed under the Apache License, Version 2.0 (the "License");
#   you may not use this file except in compliance with the License.
#   You may obtain a copy of the License at
#
#       http://www.apache.org/licenses/LICENSE-2.0
#
#   Unless required by applicable law or agreed to in writing, software
#   distributed under the License is distributed on an "AS IS" BASIS,
#   WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
#   See the License for the specific language governing permissions and
#   limitations under the License.


"""
Certificate store UI.
"""

from i18n import ChandlerMessageFactory as _

from osaf.framework.blocks import Block, NewItemEvent
from osaf.framework.blocks.detail import Detail
from osaf.framework.attributeEditors import AttributeEditorMapping
from osaf.pim.structs import SizeType, RectType
from osaf.pim import KindCollection
from osaf.usercollections import UserCollection
from osaf.framework.certstore import certificate
from application import schema


class ImportCertificateEvent(NewItemEvent):
    """
    An event used to import a new Certificate.
    """
    def onNewItem (self):
        """
        Called to create a new Item.
        """
        return certificate.importCertificateDialog(self.itsView)

def installParcel(parcel, oldVersion=None):
    # Register an extra attribute editor mapping for one of our types
    AttributeEditorMapping.register(parcel, 
        { 'typeEnum': 'osaf.framework.attributeEditors.StringAttributeEditor' },
        __name__)

    blocks    = schema.ns("osaf.framework.blocks", parcel)
    main      = schema.ns("osaf.views.main", parcel)
    # The following trick finds the location of the directory containing
    # this file. This allows us to move the parcel to a new location without
    # editing any code in it.
    certstore = schema.ns(__name__[:__name__.rfind('.')], parcel)
    detail    = schema.ns("osaf.framework.blocks.detail", parcel)

    certificateCollection = KindCollection.update(
        parcel, 'CertificateStore',
        displayName = _(u"Certificate Store"),
        kind = certstore.Certificate.getKind(parcel.itsView),
        recursive = True)
    
    #setting the preferredKind to None is a hint to display it in the All View
    UserCollection (certificateCollection).preferredKind = None

    addCertificateToSidebarEvent = Block.AddToSidebarEvent.update(
        parcel, 'addCertificateToSidebarEvent',
        blockName = 'addCertificateToSidebarEvent',
        item = certificateCollection,
        copyItems = False,
        disambiguateDisplayName = False)

    certMenu = blocks.Menu.update(
        parcel, "CertificateTestMenu",
        blockName = "CertificateTestMenu",
        title = _(u"Certificates"),
        parentBlock = main.TestMenu)

    blocks.MenuItem.update(
        parcel, "CertificateView",
        blockName = "CertificateView",
        title = _(u"Manage Certificates"),
        event = addCertificateToSidebarEvent,
        eventsForNamedLookup = [addCertificateToSidebarEvent],
        parentBlock = certMenu,
    )


    # Import
  
    importCertificateEvent = ImportCertificateEvent.update(
        parcel, 'importCertificateEvent',
        blockName = 'importCertificateEvent',
        collection = certificateCollection,
        collectionAddEvent = addCertificateToSidebarEvent,
        kindParameter = certstore.Certificate.getKind(parcel.itsView))

    blocks.MenuItem.update(
        parcel, "CertificateImport",
        blockName = "CertificateImport",
        title = _(u"Import Certificate"),
        event = importCertificateEvent,
        eventsForNamedLookup = [importCertificateEvent],
        parentBlock = certMenu,
    )

    typeArea = detail.makeArea(parcel, "TypeArea",
        position = 0.1,
        childrenBlocks = [
            detail.makeLabel(parcel, _(u'type')),
            detail.makeSpacer(parcel, width=8),
            detail.makeEditor(parcel, 'TypeAttribute',
                viewAttribute=u'type',
                stretchFactor=0.0,
                size=SizeType(60, -1)
            )]).install(parcel)
    
    trustArea = detail.makeArea(parcel, "TrustArea",
        position = 0.2,
        childrenBlocks = [
            detail.makeLabel(parcel, _(u"trust")),
            detail.makeSpacer(parcel, width=8),
            detail.makeEditor(parcel, "TrustAttribute",
                viewAttribute="trust",
                stretchFactor=0.0,
                size=SizeType(60, -1)
        )]).install(parcel)
    
    fingerprintArea = detail.makeArea(parcel, "FingerprintArea",
        position = 0.3,
        childrenBlocks = [
            detail.makeLabel(parcel, _(u"fingerprint")),
            detail.makeSpacer(parcel, width=8),
            detail.makeEditor(parcel, "FingerprintLabel",
                viewAttribute=u"fingerprint",
                stretchFactor = 0,
                size=SizeType(180, -1)
            )]).install(parcel)
    
    fingerprintAlgArea = detail.makeArea(parcel, "FingerprintAlgArea",
        position = 0.4,
        childrenBlocks = [
            detail.makeLabel(parcel, _(u"algorithm")),
            detail.makeSpacer(parcel, width=8),
            detail.makeEditor(parcel, "FingerprintAlgLabel",
                viewAttribute=u"fingerprintAlgorithm",
                stretchFactor = 0,
                size=SizeType(60, -1)
            )]).install(parcel)
    
    #XXX [i18n] Rather than getting all as text which cannot be localized,
    #XXX [i18n] make a field for each attribute in the certificate. These
    #XXX [i18n] can be localized easily. There is one blocker: there are a lot
    #XXX [i18n] of fields that should only appear if the cert has that field,
    #XXX [i18n] but there does not seem to be a way to implement that yet.
    asTextEditor = detail.makeEditor(parcel, 'AsTextAttribute',
        position = 0.9, 
        viewAttribute=u'asTextAsString',
        presentationStyle={'lineStyleEnum': 'MultiLine' },
    ).install(parcel)
    
    detail.makeSubtree(parcel, certstore.Certificate, [
        detail.MarkupBar,
        detail.makeSpacer(parcel, height=6, position=0.01).install(parcel),
        typeArea,
        trustArea,
        fingerprintArea,
        fingerprintAlgArea,
        asTextEditor,
    ])
