from Repository import RepositoryItemDetail
from osaf.framework.blocks import Tree, SplitterWindow, Column
from osaf.pim.structs import SizeType
from i18n import OSAFMessageFactory as _

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
                          Column.update(parcel, 'ColItemName',
                                        heading='ItemName',
                                        width=160),
                          Column.update(parcel, 'ColDisplayName',
                                        heading='Display Name',
                                        width=110),
                          Column.update(parcel, 'ColKind',
                                        heading='Kind',
                                        width=70),
                          Column.update(parcel, 'ColUUID',
                                        heading='UUID',
                                        width=245),
                          Column.update(parcel, 'ColPath',
                                        heading='Path',
                                        width=155),
                          ],
                          
                  size=SizeType(600,200),
                  minimumSize=SizeType(400,100)),
        RepositoryItemDetail.template('ItemDetail',
                                      size=SizeType(100,50),
                                      minimumSize=SizeType(100,50))
        ]).install(parcel)
        
    SplitterWindow.template('CPIAView',
                            displayName=u'CPIA Viewer',
                            eventBoundary=True,
                            splitPercentage=0.4,
                            childrenBlocks=[
        Tree.template('CPIATree',
                      elementDelegate='osaf.views.repositoryviewer.Repository.CPIADelegate',
                      hideRoot=False,
                      noLines=False,
                      columns = [
                          Column.update(parcel, 'ColItemName',
                                        heading='ItemName',
                                        width=160),
                          Column.update(parcel, 'ColDisplayName',
                                        heading='Display Name',
                                        width=110),
                          Column.update(parcel, 'ColKind',
                                        heading='Kind',
                                        width=70),
                          Column.update(parcel, 'ColUUID',
                                        heading='UUID',
                                        width=245),
                          Column.update(parcel, 'ColPath',
                                        heading='Path',
                                        width=155),
                          ]),
        
        RepositoryItemDetail.template('CPIAItemDetail',
                                      size=SizeType(100,50),
                                      minimumSize=SizeType(100,50))
        ]).install(parcel)

