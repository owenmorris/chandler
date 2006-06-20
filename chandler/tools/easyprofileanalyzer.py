#!/usr/bin/env python

#   Copyright (c) 2005-2006 Open Source Applications Foundation
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


import getopt, sys, os
import hotshot, hotshot.stats
import pstats
import cStringIO

        
options = { 'filename': None, 
            'order': 'time', 
            'limit': 20, 
            'output': None,
            'pager': True }

#
# process_options - processes the options from the command line
# 
def process_options():
    optlist, args = getopt.getopt(sys.argv[1:], "p:o:l:c:e:",
                                  ["profile=",
                                   "order=",
                                   "limit=",
                                   "callers-of=",
                                   "callees-of="])

    
    for opt, arg in optlist:
        if (opt == '-p'):
            options['filename'] = arg
            
        # need to check valid orders:
        # calls, cumulative, file, module, pcalls, line, name, nfl, stdname, time
        if (opt == '-o'):
            options['order'] = arg
        
        if (opt == '-l'):
            options['limit'] = int(arg)

        if (opt == '-c'):
            options['output'] = 'callers'
            options['data'] = arg

        if (opt == '-e'):
            options['output'] = 'callees'
            options['data'] = arg

    if args and not options['filename']:
        options['filename'] = args[0]

    if not options['order']:
        options['order'] = 'time'

    if not options['filename']:
        print "Filename required..."
        exit 

#
# prompt_user - prompts the user for an action, and then sets the option
#               structure to match what they entered
#
def prompt_user():
    while True:
        try:
            print "c = callers | e = callees | s = stats | o = order | l = limit";

            line = sys.stdin.readline().strip()
            
            commandline = line.split(None)
            command = commandline[0]
            if len(commandline) > 1:
                data = commandline[1]
            else:
                data = None
                
            if command == 'q':
                return False

            if command == 'c':
                options['output'] = 'callers'
                options['data'] = data

            if command == 'e':
                options['output'] = 'callees'
                options['data'] = data

            if command == 's':
                options['output'] = 'stats'
                options['data'] = data

            if command == 'o':
                options['order'] = data
                
            break
        
        except:
            print "Unrecognized command"
            
    return True

#
# output_with_pager - borrowed from http://www.andreasen.org/misc/util.py
#
def output_with_pager(string):
    print string
    
    # this seems to be broken right now?
    less = os.popen('less -', 'w')
    #try:
    less.write(string)
    less.close()
    #except:
    pass

#
# show_profile - displays the profile to the user given the current options
#
def show_profile(stats):
    # stats.strip_dirs()
    stats.sort_stats(options['order'])

    # now capture the output
    out = cStringIO.StringIO()
    old_stdout = sys.stdout
    sys.stdout = out

    # Figure out the correct part of stats to call
    try:
        if options['output'] == 'callers':
            print "    Callers of '" + options['data'] + "':"
            stats.print_callers(options['data'], options['limit'])
        elif options['output'] == 'callees':
            print "    Functions that '" + options['data'] + "' call:"
            stats.print_callees(options['data'], options['limit'])
        else:
            # show stats
            print "Statistics: "
            stats.print_stats(options['limit'])
            
    except:
        print "Couldn't generate output. Possibly bad caller/callee pattern"

    # reset to defaults
    sys.stdout = old_stdout
    out.seek(0)

    parse_state = None;

    # keep track of where the 2nd column of functions start
    # we'll find this out from the header
    col2starts = 0

    result = "";
    for line in out:

        # funclist1: the first line of the function list
        if parse_state == 'funclist':
            function = line[0:col2starts].strip()
            subfunc = line[col2starts:].strip()
            if function:
                result += "\n" + function + "\n"
            result += "        " + subfunc + "\n"

        # default parse_state, look for Function header
        elif line.startswith('Function'):
            if options['output'] == 'callers':
                col2starts = line.find('was called by')
                
            elif options['output'] == 'callees':
                col2starts = line.find('called')
                
            parse_state = 'funclist'
        else:
            result += line + "\n"

    # now spit out to less
    output_with_pager(result)

#
# main
# 
def main():

    process_options()
    
    stats = hotshot.stats.load(options['filename'])
    while prompt_user():
        show_profile(stats)


main()
