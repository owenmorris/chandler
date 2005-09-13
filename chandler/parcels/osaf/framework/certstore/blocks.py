from application import schema
from osaf.framework.certstore.certificate import (
    CertificateViewController, CertificateImportController,
    EditIntegerAttribute, AsTextAttribute
)

def installParcel(parcel, oldVersion=None):
    blocks    = schema.ns("osaf.framework.blocks", parcel)
    main      = schema.ns("osaf.views.main", parcel)
    certstore = schema.ns("osaf.framework.certstore", parcel)
    detail    = schema.ns("osaf.framework.blocks.detail", parcel)


    # View

    view_controller = CertificateViewController.update(
        parcel, "view_controller"
    )

    CertificateViewEvent = blocks.BlockEvent.update(
        parcel, "CertificateViewEvent",
        blockName = "CertificateViewBlock",
        dispatchEnum = "SendToBlockByReference",
        destinationBlockReference = view_controller,
        commitAfterDispatch = True,
    )

    blocks.MenuItem.update(
        parcel, "CertificateView",
        blockName = "CertificateView",
        title = "Manage Certificates",
        event = CertificateViewEvent,
        eventsForNamedLookup = [CertificateViewEvent],
        parentBlock = main.TestMenu,
    )


    # Import
  
    import_controller = CertificateImportController.update(
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
        title = "Import Certificate",
        event = CertificateImportEvent,
        eventsForNamedLookup = [CertificateImportEvent],
        parentBlock = main.TestMenu,
    )

    detail.DetailTrunkSubtree.update(
        parcel, "detail_subtree",
        key = certstore.Certificate.getKind(parcel.itsView),
        rootBlocks = [
            detail.MarkupBar,
            detail.DetailSynchronizedLabeledTextAttributeBlock.update(
                parcel, "TypeArea",
                position = 0.1, viewAttribute="type",
                stretchFactor = 0,
                childrenBlocks = [
                    blocks.StaticText.update(
                        parcel, "TypeLabel",
                        title = "Type",
                        characterStyle = blocks.LabelStyle,
                        stretchFactor = 0.0,
                        textAlignmentEnum = "Right",
                        minimumSize = blocks.SizeType(70, 24),
                        border = blocks.RectType(0.0, 0.0, 0.0, 5.0),
                    ),
                    detail.StaticRedirectAttribute.update(
                        parcel, "TypeAttribute",
                        title = "author",
                        characterStyle = blocks.LabelStyle,
                        stretchFactor = 0.0,
                        textAlignmentEnum = "Left",
                    ),
                ]                    
            ),

            detail.DetailSynchronizedLabeledTextAttributeBlock.update(
                parcel, "TrustArea",
                position = 0.2, viewAttribute="trust",
                stretchFactor = 0,
                childrenBlocks = [
                    blocks.StaticText.update(
                        parcel, "TrustLabel",
                        title = "Trust",
                        characterStyle = blocks.LabelStyle,
                        stretchFactor = 0.0,
                        textAlignmentEnum = "Right",
                        minimumSize = blocks.SizeType(70, 24),
                        border = blocks.RectType(0.0, 0.0, 0.0, 5.0),
                    ),
                    EditIntegerAttribute.update(
                        parcel, "TrustAttribute",
                        lineStyleEnum = "SingleLine",
                        textStyleEnum = "PlainText",
                        characterStyle = blocks.TextStyle,
                        readOnly = False,
                        textAlignmentEnum = "Left",
                        minimumSize = blocks.SizeType(50, 24),
                    ),
                ]                    
            ),

            detail.DetailSynchronizedLabeledTextAttributeBlock.update(
                parcel, "FingerprintArea",
                position = 0.3, viewAttribute="fingerprint",
                stretchFactor = 0,
                childrenBlocks = [
                    detail.DetailSynchronizedLabeledTextAttributeBlock.update(
                        parcel, "FingerprintLabel",
                        position = 0.3,
                        viewAttribute="fingerprintAlgorithm",
                        stretchFactor = 0,
                        childrenBlocks = [
                            detail.StaticRedirectAttribute.update(
                                parcel, "FingerprintAlgorithmAttribute",
                                title = "author",   # sic!
                                characterStyle = blocks.LabelStyle,
                                stretchFactor = 0.0,
                                textAlignmentEnum = "Right",
                                minimumSize = blocks.SizeType(70, 24),
                                border = blocks.RectType(0.0, 0.0, 0.0, 5.0),
                            ),
                        ],
                    ),
                    detail.StaticRedirectAttribute.update(
                        parcel, "FingerprintAttribute",
                        title = "author",   # sic!
                        characterStyle = blocks.LabelStyle,
                        stretchFactor = 0.0,
                        textAlignmentEnum = "Left",
                    )
                ],
            ),

            detail.DetailSynchronizedLabeledTextAttributeBlock.update(
                parcel, "AsTextArea",
                position = 0.9, viewAttribute="asText",
                stretchFactor = 1,
                childrenBlocks = [
                    AsTextAttribute.update(
                        parcel, "AsTextAttribute",
                        characterStyle = blocks.TextStyle,
                        lineStyleEnum = "MultiLine",
                        textStyleEnum = "PlainText",
                        readOnly = True,
                        textAlignmentEnum = "Left",
                    ),
                ],
            ),
        ],
    )

