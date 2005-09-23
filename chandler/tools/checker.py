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
