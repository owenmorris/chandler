#!/bin/env python
# -*- coding: utf-8 -*-

#   Copyright (c) 2006-2007 Open Source Applications Foundation
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

from setuptools import setup


setup(
    name         = "Chandler",
    version      = "0.1",
    author       = "Brian Kirsch",
    author_email = "bkirsch@osafoundation.org",
    description  = "Default resource and localization egg for Chandler",
    license      = "Apache License, Version 2.0",
    test_suite   = 'unittest.TestCase',
    include_package_data = True,
    zip_safe             = True,
    entry_points = {"chandler.parcels": ["Script Recording = osaf.framework.script_recording"]
                   }
)

