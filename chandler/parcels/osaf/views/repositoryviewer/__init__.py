from Repository import RepositoryItemDetail
from osaf.framework.blocks import Tree, SplitterWindow
from osaf.framework.types.DocumentTypes import SizeType
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
                  columnHeadings=[
                      u'ItemName',
                      u'Display Name',
                      u'Kind',
                      u'UUID',
                      u'Path',
                  ],
                  columnWidths=[160, 110, 70, 245, 155],
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
                      columnHeadings=[
            u'Block Name',
            u'Kind',
            u'Display Name',
            u'UUID',
            u'Path'
            ],
                      columnWidths=[160,110,70, 245, 155]),
        RepositoryItemDetail.template('CPIAItemDetail',
                                      size=SizeType(100,50),
                                      minimumSize=SizeType(100,50))
        ]).install(parcel)

