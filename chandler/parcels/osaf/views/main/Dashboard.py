"""
Stuff related to the dashboard
"""

from application import schema
from osaf.framework import Preferences
from osaf.framework.blocks import Table


class DashboardPrefs(Preferences):

    showSections = schema.One(schema.Boolean, defaultValue = False)
    
    
class DashboardBlock(Table):
    """
    A block class for the Chandler Dashboard.

    This class works with the expectation that the delegate is the
    SectionedGridDelegate from the Sections module.
    """
    
    def render(self, *args, **kwds):
        super(DashboardBlock, self).render(*args, **kwds)

        if __debug__:
            from Sections import SectionedGridDelegate
            assert isinstance(self.widget, SectionedGridDelegate)

        view = self.itsView
        prefs = schema.ns('osaf.views.main', view).dashboardPrefs
        view.watchItem(self, prefs, 'onEnableSectionsPref')
        
    def onDestroyWidget(self, *args, **kwds):
        view = self.itsView
        prefs = schema.ns('osaf.views.main', view).dashboardPrefs
        view.unwatchItem(self, prefs, 'onEnableSectionsPref')
        
        super(DashboardBlock, self).onDestroyWidget(*args, **kwds)

    def onEnableSectionsPref(self, op, item, names):
        if 'showSections' in names:
            self.synchronizeWidget()
