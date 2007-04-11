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


import os
import hotshot, hotshot.stats, pstats

def cum(stats, length=50):
    stats.sort_stats('cum')
    stats.print_stats(length)

def calls(stats, length=50):
    stats.sort_stats('time', 'calls')
    stats.print_stats(length)

def show(file, call='cum', length=50):
    if file.endswith('stats'):
        stats = pstats.Stats(file)
    else:
        stats = hotshot.stats.load(file)
        stats.strip_dirs()
        stats.dump_stats('.'.join((os.path.splitext(file)[0], 'stats')))
    if call == 'cum':
        cum(stats, int(length))
    elif call == 'tot':
        calls(stats, int(length))
    else:
        stats.sort_stats(call)
        stats.print_stats(int(length))

    stats.print_callers(int(length))
    stats.print_callees(int(length))
    return stats

if __name__ == "__main__":
    from sys import argv
    show(*argv[1:])

