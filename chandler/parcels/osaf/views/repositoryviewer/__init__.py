from Repository import RepositoryItemDetail, BlockItemDetail
from osaf.framework.blocks import Tree, SplitterWindow, Column
from osaf.pim.structs import SizeType
from i18n import OSAFMessageFactory as _
from osaf.framework.blocks import FrameWindow

def installParcel(parcel, oldName=None):

    SplitterWindow.template('RepositoryView',
                            displayName=u'Repository Viewer',
                            eventBoundary=True,
                            splitPercentage=0.40,
                            childrenBlocks=[
        Tree.template('RepositoryTree',
                  elementDelegate='osaf.views.repositoryviewer.Repository.RepositoryDelegate',
                  hideRoot=False,
                  noLines=False,
                      columns = [
                          Column.update(parcel, 'RepositoryViewColItemName',
                                        heading='ItemName',
                                        width=160),
                          Column.update(parcel, 'RepositoryViewColDisplayName',
                                        heading='Display Name',
                                        width=110),
                          Column.update(parcel, 'RepositoryViewColKind',
                                        heading='Kind',
                                        width=70),
                          Column.update(parcel, 'RepositoryViewColUUID',
                                        heading='UUID',
                                        width=245),
                          Column.update(parcel, 'RepositoryViewColPath',
                                        heading='Path',
                                        width=155),
                          ],
                          
                  size=SizeType(600,200),
                  minimumSize=SizeType(400,100)),
        RepositoryItemDetail.template('ItemDetail',
                                      size=SizeType(100,50))
        ]).install(parcel)

    FrameWindow.template(
        'BlockViewerFrameWindow',
        size=SizeType(768, 512),
        windowTitle = _(u"Block Viewer"),
        eventBoundary=True,
        childrenBlocks = [
            SplitterWindow.template(
                'Splitter',
                eventBoundary=True,
                splitPercentage=0.4,
                childrenBlocks=[
                    Tree.template(
                        'Tree',
                        elementDelegate='osaf.views.repositoryviewer.Repository.BlockDelegate',
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
                    
                    BlockItemDetail.template(
                        'CPIAItemDetail',
                        size=SizeType(100,50))
                ])
        ]).install(parcel)
