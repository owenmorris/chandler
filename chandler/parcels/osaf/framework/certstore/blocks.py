"""
Certificate store UI.

@copyright: Copyright (c) 2005 Open Source Applications Foundation
@license:   http://osafoundation.org/Chandler_0.1_license_terms.htm
"""

from i18n import OSAFMessageFactory as _

from osaf.framework.blocks import Block
from osaf.framework.blocks.detail import Detail
from osaf.framework.types.DocumentTypes import SizeType, RectType
from osaf.pim import KindCollection

class _CertificateImportController(Block.Block):
    def onCertificateImportBlockEvent(self, event):
        from osaf.framework.certstore import certificate
        certificate.importCertificateDialog(self.itsView)

class _EditIntegerAttribute (Detail.EditTextAttribute):
    #XXX Get rid of this as soon as boolean editors work with properties
    def saveAttributeFromWidget(self, item, widget, validate):
        if validate:
            item.setAttributeValue(self.whichAttribute(),
                                   int(widget.GetValue()))

    def loadAttributeIntoWidget(self, item, widget):
        try:
            value = item.getAttributeValue(self.whichAttribute())
        except AttributeError:
            value = 0
        wiVal = widget.GetValue()
        if not wiVal or int(wiVal) != value:
            widget.SetValue(unicode(value))


class _AsTextAttribute (Detail.EditTextAttribute):
    #XXX Get rid of this, asText should be normal (readonly) value
    def saveAttributeFromWidget(self, item, widget, validate):
        pass

    def loadAttributeIntoWidget(self, item, widget):
        value = item.asTextAsString()
        if widget.GetValue() != value:
            widget.SetValue(value)


def installParcel(parcel, oldVersion=None):
    from application import schema

    blocks    = schema.ns("osaf.framework.blocks", parcel)
    main      = schema.ns("osaf.views.main", parcel)
    certstore = schema.ns("osaf.framework.certstore", parcel)
    detail    = schema.ns("osaf.framework.blocks.detail", parcel)

    certStore = KindCollection.update(
        parcel, 'CertificateStore',
        displayName = _(u"Certificate Store"),
        kind = certstore.Certificate.getKind(parcel.itsView),
        recursive = True).setup()

    addCertificateToSidebarEvent = Block.ModifyCollectionEvent.template(
        'addCertificateToSidebarEvent',
        methodName = 'onModifyCollectionEvent',
        dispatchToBlockName = 'MainView',
        selectInBlockNamed = 'Sidebar',
        items = [certStore],
        dispatchEnum = 'SendToBlockByName').install(parcel)

    blocks.MenuItem.update(
        parcel, "CertificateView",
        blockName = "CertificateView",
        title = u"Manage Certificates",
        event = addCertificateToSidebarEvent,
        eventsForNamedLookup = [addCertificateToSidebarEvent],
        parentBlock = main.TestMenu,
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
        title = u"Import Certificate",
        event = CertificateImportEvent,
        eventsForNamedLookup = [CertificateImportEvent],
        parentBlock = main.TestMenu,
    )

    detail.makeSubtree(parcel, certstore.Certificate, [
        detail.MarkupBar,
        detail.DetailSynchronizedLabeledTextAttributeBlock.update(
            parcel, "TypeArea",
            position = 0.1, viewAttribute=u"type",
            stretchFactor = 0,
            childrenBlocks = [
                blocks.StaticText.update(
                    parcel, "TypeLabel",
                    title = _(u"Type"),
                    characterStyle = blocks.LabelStyle,
                    stretchFactor = 0.0,
                    textAlignmentEnum = "Right",
                    minimumSize = SizeType(70, 24),
                    border = RectType(0.0, 0.0, 0.0, 5.0),
                ),
                detail.StaticRedirectAttribute.update(
                    parcel, "TypeAttribute",
                    title = u"author",
                    characterStyle = blocks.LabelStyle,
                    stretchFactor = 0.0,
                    textAlignmentEnum = "Left",
                ),
            ]                    
        ),

        detail.DetailSynchronizedLabeledTextAttributeBlock.update(
            parcel, "TrustArea",
            position = 0.2, viewAttribute=u"trust",
            stretchFactor = 0,
            childrenBlocks = [
                blocks.StaticText.update(
                    parcel, "TrustLabel",
                    title = _(u"Trust"),
                    characterStyle = blocks.LabelStyle,
                    stretchFactor = 0.0,
                    textAlignmentEnum = "Right",
                    minimumSize = SizeType(70, 24),
                    border = RectType(0.0, 0.0, 0.0, 5.0),
                ),
                _EditIntegerAttribute.update(
                    parcel, "TrustAttribute",
                    lineStyleEnum = "SingleLine",
                    textStyleEnum = "PlainText",
                    characterStyle = blocks.TextStyle,
                    readOnly = False,
                    textAlignmentEnum = "Left",
                    minimumSize = SizeType(50, 24),
                ),
            ]                    
        ),

        detail.DetailSynchronizedLabeledTextAttributeBlock.update(
            parcel, "FingerprintArea",
            position = 0.3, viewAttribute=u"fingerprint",
            stretchFactor = 0,
            childrenBlocks = [
                detail.DetailSynchronizedLabeledTextAttributeBlock.update(
                    parcel, "FingerprintLabel",
                    position = 0.3,
                    viewAttribute=u"fingerprintAlgorithm",
                    stretchFactor = 0,
                    childrenBlocks = [
                        detail.StaticRedirectAttribute.update(
                            parcel, "FingerprintAlgorithmAttribute",
                            title = u"author",   # sic!
                            characterStyle = blocks.LabelStyle,
                            stretchFactor = 0.0,
                            textAlignmentEnum = "Right",
                            minimumSize = SizeType(70, 24),
                            border = RectType(0.0, 0.0, 0.0, 5.0),
                        ),
                    ],
                ),
                detail.StaticRedirectAttribute.update(
                    parcel, "FingerprintAttribute",
                    title = u"author",   # sic!
                    characterStyle = blocks.LabelStyle,
                    stretchFactor = 0.0,
                    textAlignmentEnum = "Left",
                )
            ],
        ),

        detail.DetailSynchronizedLabeledTextAttributeBlock.update(
            parcel, "AsTextArea",
            position = 0.9, viewAttribute=u"asText",
            stretchFactor = 1,
            childrenBlocks = [
                _AsTextAttribute.update(
                    parcel, "AsTextAttribute",
                    characterStyle = blocks.TextStyle,
                    lineStyleEnum = "MultiLine",
                    textStyleEnum = "PlainText",
                    readOnly = True,
                    textAlignmentEnum = "Left",
                ),
            ],
        )])
