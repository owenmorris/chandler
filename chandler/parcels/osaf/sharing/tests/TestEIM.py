import unittest
from util.test_finder import ScanningLoader
unittest.main(                        
        module=None, testLoader = ScanningLoader(),
        argv=["unittest", "osaf.sharing.eim.test_suite"]                            
)


