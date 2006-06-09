from Repository import RepositoryItemDetail
from osaf.framework.blocks import Tree, SplitterWindow, Column
from osaf.pim.structs import SizeType, RectType
from i18n import OSAFMessageFactory as _
from osaf.framework.blocks import FrameWindow, BoxContainer

def installParcel(parcel, oldName=None):

    FrameWindow.template(
        'RepositoryViewerFrameWindow',
        size=SizeType(768, 512),
        windowTitle = _(u"Repository Viewer"),
        eventBoundary=True,
        childrenBlocks = [
            SplitterWindow.template(
                'RepositoryView',
                displayName=u'Repository Viewer',
                eventBoundary=True,
                splitPercentage=0.5,
                childrenBlocks=[
                    Tree.template(
                        'RepositoryTree',
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
                    BoxContainer.template('RepositoryItemDetailContainer',
                        border = RectType(4, 0, 0, 0),
                        childrenBlocks = [
                            RepositoryItemDetail.template('RepositoryItemDetail',
                                                          size=SizeType(-1,-1))
                            ])
                    ])
            ]).install(parcel)

