#   Copyright (c) 2003-2007 Open Source Applications Foundation
#
#   Licensed under the Apache License, Version 2.0 (the "License");
#   you may not use this file except in compliance with the License.
#   You may obtain a copy of the License at
#
#       http://www.apache.org/licenses/LICENSE-2.0
#
#   Unless required by applicable law or agreed to in writing, software
#   distributed under the License is distributed on an "AS IS" BASIS,
#   WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
#   See the License for the specific language governing permissions and
#   limitations under the License.


import unittest, os
from repository.tests.RepositoryTestCase import RepositoryTestCase
from osaf import sharing

class TestLargeImport(RepositoryTestCase):

    def testImport(self):
        if os.environ.get('CHANDLER_PERFORMANCE_TEST'):
            self.loadParcel("osaf.pim.calendar")
            path = os.path.join(os.getenv('CHANDLERHOME') or '.',
                                'parcels', 'osaf', 'sharing', 'tests')

            share = sharing.shares.OneTimeFileSystemShare(
                itsView=self.view, 
                filePath=path, fileName=u"3kevents.ics",
                translatorClass=sharing.translator.SharingTranslator,
                serializerClass=sharing.ics.ICSSerializer
            )
            
            share._prepare()

            share.get()


if __name__ == "__main__":
    unittest.main()
