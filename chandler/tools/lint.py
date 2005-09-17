"""
Find problems in Python code

Run ./release/RunPython tools/lint.py --help for options

Without arguments runs a Chandler-specific report.
"""

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
    sys.argv.append('util')
    sys.argv.append('version')

from pylint import lint
lint.Run(sys.argv[1:])
