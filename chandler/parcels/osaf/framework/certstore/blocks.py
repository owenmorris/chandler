"""
Certificate store UI.

@copyright: Copyright (c) 2005 Open Source Applications Foundation
@license:   http://osafoundation.org/Chandler_0.1_license_terms.htm
"""

from i18n import OSAFMessageFactory as _

from osaf.framework.blocks import Block
from osaf.framework.blocks.detail import Detail
from osaf.framework.attributeEditors import AttributeEditorMapping
from osaf.pim.structs import SizeType, RectType
from osaf.pim import KindCollection

class _CertificateImportController(Block.Block):
    def onCertificateImportBlockEvent(self, event):
        from osaf.framework.certstore import certificate
        certificate.importCertificateDialog(self.itsView)

def installParcel(parcel, oldVersion=None):
    from application import schema

    # Register an extra attribute editor mapping for one of our types
    AttributeEditorMapping.register(parcel, 
        { 'typeEnum': 'osaf.framework.attributeEditors.StringAttributeEditor' },
        __name__)

    blocks    = schema.ns("osaf.framework.blocks", parcel)
    main      = schema.ns("osaf.views.main", parcel)
    certstore = schema.ns("osaf.framework.certstore", parcel)
    detail    = schema.ns("osaf.framework.blocks.detail", parcel)

    certStore = KindCollection.update(
        parcel, 'CertificateStore',
        displayName = _(u"Certificate Store"),
        kind = certstore.Certificate.getKind(parcel.itsView),
        recursive = True)

    addCertificateToSidebarEvent = Block.ModifyCollectionEvent.template(
        'addCertificateToSidebarEvent',
        methodName = 'onModifyCollectionEvent',
        dispatchToBlockName = 'MainView',
        selectInBlockNamed = 'Sidebar',
        items = [certStore],
        dispatchEnum = 'SendToBlockByName').install(parcel)

    certMenu = blocks.Menu.update(
        parcel, "CertificateTestMenu",
        blockName = "CertificateTestMenu",
        title = _(u"Certificates"),
        parentBlock = main.TestMenu,
        )

    blocks.MenuItem.update(
        parcel, "CertificateView",
        blockName = "CertificateView",
        title = _(u"Manage Certificates"),
        event = addCertificateToSidebarEvent,
        eventsForNamedLookup = [addCertificateToSidebarEvent],
        parentBlock = certMenu,
    )


    # Import
  
    import_controller = _CertificateImportController.update(
        parcel, "CertificateImportController"
    )

    CertificateImportEvent = blocks.BlockEvent.update(
        parcel, "CertificateImportEvent",
        blockName = "CertificateImportBlock",
        dispatchEnum = "SendToBlockByReference",
        destinationBlockReference = import_controller,
        commitAfterDispatch = True,
    )

    blocks.MenuItem.update(
        parcel, "CertificateImport",
        blockName = "CertificateImport",
        title = _(u"Import Certificate"),
        event = CertificateImportEvent,
        eventsForNamedLookup = [CertificateImportEvent],
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
