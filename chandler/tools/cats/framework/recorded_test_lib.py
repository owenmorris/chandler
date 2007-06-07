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

executed_dependencies = []

def account_settings():
    
    import os, sys
    from osaf import settings
    import wx
    
    settings_file = os.path.abspath(
                      os.path.join(
                        os.path.dirname(os.path.abspath(sys.modules[__name__].__file__)),
                        os.path.pardir,
                        'DataFiles',
                        'demo1Settings.ini'
                        ))
                   
    settings.restore(wx.GetApp().UIRepositoryView, settings_file)
	

