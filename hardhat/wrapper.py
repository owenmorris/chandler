#!/usr/bin/python

import sys, os, os.path

def quoteString(str):
    return "\'" + str + "\'"

def escapeBackslashes(str):
    return str.replace("\\", "\\\\")

def executeCommand(logfile, showenv, args):

    # print "incoming args:"
    # for arg in args:
    #     print arg

    # if os.path.exists( args[0] ):
    #     print args[0], "exists"
    # else:
    #     print args[0], "doesn't exist"

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
