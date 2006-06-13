# Create script file end.py: import sys; sys.exit(0)
# Create a new repository by starting Chandler with --create
# Start Chandler 3 times with: time chandler -f end.py
# Pick the run whose time was in the middle (the "real" time row)

import tools.cats.framework.ChandlerTestLib as QAUITestAppLib
from tools.cats.framework.ChandlerTestCase import ChandlerTestCase

class end(ChandlerTestCase):

    def startTest(self):

        QAUITestAppLib.App_ns.root.Quit()
        
        import sys;
        sys.exit(0)
