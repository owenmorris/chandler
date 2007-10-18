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

from datetime import datetime

now = None

def getNow(tz=None):
    """
    Return the current datetime in timezone tz, or the timemachine's pretend
    time.  Return the time in timezone tz if tz isn't None.
    
    """
    if now is None:
        return datetime.now(tz=tz)
    elif tz is None:
        return now
    else:
        return now.astimezone(tz)

def setNow(dt):
    global now
    now = dt
    
def resetNow():
    setNow(None)
