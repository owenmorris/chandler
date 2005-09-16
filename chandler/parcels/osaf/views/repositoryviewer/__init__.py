from Repository import RepositoryItemDetail
from osaf.framework.blocks import Tree, SplitterWindow, SizeType
from i18n import OSAFMessageFactory as _

def installParcel(parcel, oldName=None):

    SplitterWindow.template('RepositoryView',
                            displayName=_(u'Repository Viewer'),
                            eventBoundary=True,
                            splitPercentage=0.40,
                            childrenBlocks=[
        Tree.template('RepositoryTree',
                  elementDelegate='osaf.views.repositoryviewer.Repository.RepositoryDelegate',
                  hideRoot=False,
                  noLines=False,
                  columnHeadings=[
                      _(u'ItemName'),
                      _(u'Display Name'),
                      _(u'Kind'),
                      _(u'UUID'),
                      _(u'Path'),
                  ],
                  columnWidths=[160, 110, 70, 245, 155],
                  size=SizeType(600,200),
                  minimumSize=SizeType(400,100)),
        RepositoryItemDetail.template('ItemDetail',
                                      size=SizeType(100,50),
                                      minimumSize=SizeType(100,50))
        ]).install(parcel)
        
    SplitterWindow.template('CPIAView',
                            displayName=_(u'CPIA Viewer'),
                            eventBoundary=True,
                            splitPercentage=0.4,
                            childrenBlocks=[
        Tree.template('CPIATree',
                      elementDelegate='osaf.views.repositoryviewer.Repository.CPIADelegate',
                      hideRoot=False,
                      noLines=False,
                      columnHeadings=[
            _(u'Block Name'),
            _(u'Kind'),
            _(u'Display Name'),
            _(u'UUID'),
            _(u'Path')
            ],
                      columnWidths=[160,110,70, 245, 155]),
        RepositoryItemDetail.template('CPIAItemDetail',
                                      size=SizeType(100,50),
                                      minimumSize=SizeType(100,50))
        ]).install(parcel)

