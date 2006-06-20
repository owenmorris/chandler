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
Find problems in Python code

Run ./release/RunPython tools/lint.py --help for options

Without arguments runs a Chandler-specific report.
"""

if __name__ == '__main__':
    import sys
    
    if len(sys.argv) == 1:
        sys.argv.append('--disable-msg-cat=R,C')
        sys.argv.append('--disable-msg=W0103,W0131,C0103,W0142,W0312,W0511,W0232,W0201,E0214,W0613,W0401')
        #sys.argv.append('--disable-report=R0001,R0002,R0003,R0004,R0701,R0801,R0401,R0101')
        sys.argv.append('--include-ids=y')
        sys.argv.append('Chandler')
        sys.argv.append('application')
        sys.argv.append('i18n')
        sys.argv.append('osaf')
        sys.argv.append('repository')
        sys.argv.append('tools')
        sys.argv.append('util')
        sys.argv.append('version')
    
    from pylint import lint
    lint.Run(sys.argv[1:])
