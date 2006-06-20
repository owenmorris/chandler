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


"""
Find problems in Python code using PyChecker

Run ./release/RunPython tools/checker.py

Without arguments runs a Chandler-specific report. Some modules
not handled.

See U{PyChecker manual<http://pychecker.sourceforge.net/>} for specifying
options.
"""

if __name__ == '__main__':
    import sys
    
    if len(sys.argv) == 1:
        sys.argv.append('Chandler')
        sys.argv.append('application')
        sys.argv.append('i18n')
        sys.argv.append('parcels/osaf')
        sys.argv.append('repository')
        sys.argv.append('tools')
        sys.argv.append('util')
        sys.argv.append('version')
        
    from pychecker import checker
    checker.main(sys.argv)
