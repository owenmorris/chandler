#!/usr/bin/python

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


import sys, os, os.path

def quoteString(str):
    return "\'" + str + "\'"

def unescapeSpaces(str):
    return str.replace("|", " ")

def escapeBackslashes(str):
    return str.replace("\\", "\\\\")

def executeCommand(logfile, showenv, args):

    # print "incoming args:"
    # for arg in args:
    #     print arg

    if os.name == 'nt' and sys.platform != 'cygwin':
        args[0] = unescapeSpaces(args[0])

    if os.path.exists( args[0] ):
        # print args[0], "exists"
        pass
    else:
        print args[0], "doesn't exist"
        return 127 # file not found

    args = map(escapeBackslashes, args)

    # since spawnl wants the name of the file we're executing twice, let's 
    # prepend it to the list...
    args[:0] = [args[0]]  

    # ...but strip out the path of the executable in args[1]
    args[1] = os.path.basename(args[1]) 

    # all args need to be quoted
    args = map(quoteString, args)

    args_str = ','.join(args)
    execute_str = "exit_code = os.spawnl(os.P_WAIT," + args_str + ")"
    # print execute_str

    output = file(logfile, 'a+', 0)


    os.dup2(output.fileno(), sys.stdout.fileno())
    os.dup2(output.fileno(), sys.stderr.fileno())

    output.write("Executing: ")
    output.write(" ".join(args[0:]))
    output.write("\n")
    output.write("Current directory: ")
    output.write(os.getcwd())
    output.write("\n")

    if showenv == "yes":
        output.write("- - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - env -\n")
        env = os.environ.keys()
        env.sort()
        for e in env:
            output.write("- " + e + "=" + os.environ[e] + "\n")

    output.write("- - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - start -\n")


    exec( execute_str )

    output.write("- - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - end - -\n")
    os.close(output.fileno())

    return exit_code

exit_code = executeCommand(sys.argv[1], sys.argv[2], sys.argv[3:])
sys.exit( exit_code )
