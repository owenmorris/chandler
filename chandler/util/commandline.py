#!/usr/bin/env python
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

from osaf import pim
from osaf.pim.calendar import Calendar
import datetime, time

def execute_command(view, text):
    """
    Parse a piece of text containing a command and execute it in the
    provided view

    /create [note|event|task] "text"

    Form of text:
    * For note - [the text of the note]
    * For an event - [date] [length] [title of the event]::
      format for date = '%Y-%m-%dT%H:%M:%S'
      format for length    '%H:%M:%S'
    * For a task - [title of the task]

    ## find the original command line thread
    """

    first_space = text.find(' ')
    command = text[:first_space]
    second_space = text.find(' ',first_space+1)
    subcommand = text[first_space+1:second_space]
    data = text[second_space+1:]

    if command == '/create':
        process_create(view, subcommand, data)

fmt = '%Y-%m-%dT%H:%M:%S'

def parse_datetime(s):
    fmt = '%Y-%m-%dT%H:%M:%S'
    (y,m,d,h,min,s,wd,yd,tz) = time.strptime(s, fmt)
    return datetime.datetime(y,m,d,h,min,s)

def parse_timedelta(s):
    fmt = '%H:%M:%S'
    (y,mo,d,h,m,s,wd,yd,tz) = time.strptime(s, fmt)
    return datetime.timedelta(hours=h, minutes=m, seconds=s)

def process_create(view, subcommand, text):
    if subcommand == 'note':
        note = pim.Note(itsView=view, displayName=text)
        view.commit()
    elif subcommand == 'event':
        first_space = text.find(' ')
        s = text[:first_space]
        second_space = text.find(' ',first_space+1)
        l = text[first_space+1:second_space]
        data = text[second_space+1:]

        start = parse_datetime(s)
        length = parse_timedelta(l)
        task = Calendar.CalendarEvent(itsView=view, startTime=start , duration=length )
        view.commit()
    elif subcommand == 'task':
        task = pim.Task(itsView=view, displayName=text)
        view.commit()
    else:
        print "illegal create subcomand"


if __name__ == "__main__":
    from optparse import OptionParser

    parser = OptionParser()

    (options, args) = parser.parse_args()

    # just some simple tests
    execute_command(None, '/create note hello world!')
    execute_command(None, '/create task hello world!')
    execute_command(None, '/create event 2005-01-19T18:05:01 1:0:0 demo')
