#!/bin/sh
#   Copyright (c) 2007 Open Source Applications Foundation
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

# Run tests in a nested X Server. This way you can launch functional or
# performance tests (although don't time performance tests this way) and
# continue other work. You can even minimize the nested X Server window.

# Using the Xephyr nested X Server, launcing on display 1
Xephyr :1 -ac -br -screen 1280x1024&

# Start metacity and an auxiliary console
metacity --display=:1&
xterm -sb -rightbar -display :1&

# Now run the actual tests and sleep a long time so you can read the results
# from the terminal.
xterm -sb -rightbar -display :1 -geometry -0-30 -e "cd `pwd` && ./tools/rt.py $* && sleep 7d || sleep 7d"&
