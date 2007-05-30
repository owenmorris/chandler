#!/usr/bin/env python
#Expected lines like this:
#date    |time  |testidentifier                              | rev  | secs
#20070220|223243|repository.tests.testdelete.testclouddelete | 1234 | 0.00027

import re

compiled = re.compile('^20[0-9]{6}\|[0-9]{6}\|[a-zA-Z0-9\.\_\-]+ +\| [0-9]+ \| [0-9]+\.[0-9]+')
f = open('new_win.dat', 'w')
b = open('bad_win.dat', 'w')
for line in open('p_win.dat'):
    if compiled.match(line):
        f.write(line)
    else:
    	b.write(line)
f.close()
b.close()