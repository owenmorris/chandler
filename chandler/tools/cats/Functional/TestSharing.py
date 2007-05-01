#   Copyright (c) 2003-2006 Open Source Applications Foundation
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

import tools.cats.framework.ChandlerTestLib as QAUITestAppLib
import os, sys
from application.dialogs.PublishCollection import ShowPublishDialog
import wx
from i18n import ChandlerMessageFactory as _
import tools.cats.framework.ChandlerTestLib as QAUITestAppLib
from tools.cats.framework.ChandlerTestCase import ChandlerTestCase
import osaf.pim as pim
from i18n.tests import uw
from osaf.framework.blocks.Block import Block
from repository.item.Item import MissingClass


class TestSharing(ChandlerTestCase):

    def startTest(self):
        # If we don't have this there'll be a mysterious error:
        # AttributeError: 'Panel' object has no attribute 'GetValue'
        QAUITestAppLib.UITestItem("Collection", self.logger)

        QAUITestAppLib.publishSubscribe(self)
