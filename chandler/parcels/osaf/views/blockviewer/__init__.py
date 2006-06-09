from blockviewer import BlockItemDetail
from osaf.framework.blocks import Tree, SplitterWindow, Column
from osaf.pim.structs import SizeType, RectType
from i18n import OSAFMessageFactory as _
from osaf.framework.blocks import FrameWindow, BoxContainer

def installParcel(parcel, oldName=None):

    FrameWindow.template(
        'BlockViewerFrameWindow',
        size=SizeType(768, 512),
        windowTitle = _(u"Block Viewer"),
        eventBoundary=True,
        childrenBlocks = [
            SplitterWindow.template(
                'Splitter',
                eventBoundary=True,
                splitPercentage=0.5,
                stretchFactor=1.0,
                childrenBlocks=[
                    Tree.template(
                        'Tree',
                        elementDelegate='osaf.views.blockviewer.blockviewer.BlockDelegate',
                        hideRoot=False,
                        noLines=False,
                        columns = [
                            Column.update(
                                parcel, 'ColumnBlockName',
                                heading='BlockName',
                                width=350),
                            Column.update(
                                parcel, 'ColumnKind',
                                heading='Kind',
                                width=100),
                            Column.update(
                                parcel, 'ColumnWidget',
                                heading='Widget',
                                width=280),
                            Column.update(
                                parcel, 'ColumnUUID',
                                heading='UUID',
                                width=40),
                            ]),
                    
                    BoxContainer.template('BlockItemDetailContainer',
                        border = RectType(4, 0, 0, 0),
                        childrenBlocks = [
                            BlockItemDetail.template(
                                'BlockItemDetail',
                                size=SizeType(-1,-1))
                            ])
                    ])
            ]).install(parcel)
