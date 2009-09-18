//
//  Copyright (c) 2009 Open Source Applications Foundation
//
//  Licensed under the Apache License, Version 2.0 (the "License");
//  you may not use this file except in compliance with the License.
//  You may obtain a copy of the License at
//
//      http://www.apache.org/licenses/LICENSE-2.0
//
//  Unless required by applicable law or agreed to in writing, software
//  distributed under the License is distributed on an "AS IS" BASIS,
//  WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
//  See the License for the specific language governing permissions and
//  limitations under the License.
//
#import <Foundation/Foundation.h>
#import <python.h>
#import <stdarg.h>
#import <libc.h>
#import <mach-o/dyld.h>

static void SetEnv(NSString *key, id value) {
    // Utility to set an environment variable, since there doesn't
    // seem to be one in Foundation.
#if defined(DEBUG)
    NSLog(@"export %@=%@", key, value);
#endif
    NSString *stringValue;

    if ([value isKindOfClass:[NSArray class]]) {
        stringValue = [(NSArray *)value componentsJoinedByString:@":"];
    } else if ([value isKindOfClass:[NSString class]]) {
        stringValue = (NSString *)value;
    } else {
        stringValue = [value description];
    }   
    setenv([key UTF8String], [stringValue fileSystemRepresentation], 1);
}

int main(int argc, char *argv[]) {

    // This program is essentially the binary equivalent of the Chandler
    // script used on Mac OS X 10.4 (or its Linux equivalent
    // chandler/chandlerDebug). It is custom-made to work inside
    // a .app bundle (i.e. will fail if it can't find a Chandler.py
    // in exactly the right place).
    //
    // TODO: ChandlerApp had a trick (checking for -E in sys.argv) that
    // still needs to be replicated here (it allowed plugins to load).

    NSAutoreleasePool *pool = [NSAutoreleasePool new];
    NSDictionary *env = [[NSProcessInfo processInfo] environment];
    NSBundle *bundle = [NSBundle mainBundle];
    NSString *resdir = [bundle resourcePath];

    // Check for Chandler.py, and bail if not present.
    NSString *mainPath = [bundle pathForResource:@"Chandler" ofType:@"py"];
    if (nil == mainPath) {
        NSLog(@"*** This program is designed to be installed inside a .app wrapper. Please use the RunPython script instead.");
        exit(1);
    }
    
    if (nil == [env objectForKey:@"DYLD_LIBRARY_PATH"]) {
        // Check for a GDB environment variable. If that is set, try
        // to exec it instead, for debugging convenience.
        if (nil != [env objectForKey:@"GDB"]) {
            // 3 + argc here: 2 for "gdb", "--args", 1 for NULL
            const char **newArgv = (const char **)calloc(3 + argc, sizeof(char *));
            unsigned index;
            newArgv[0] = "/usr/bin/gdb";
            newArgv[1] = "--args";
            memcpy(&newArgv[2], argv, argc * sizeof(char *));
            newArgv[2 + argc] = NULL;
            
            for(index=0; index<argc; index++) {
                newArgv[index+2] = argv[index];
            }
            
            argv = (char **)newArgv;
        }
        
        // Load up DYLD_LIBRARY_PATH, and re-exec ourselves. It
        // would be nice if the OSX linker were cleverer and allowed
        // you to reconfigure it at runtime, but sadly, no.
        SetEnv(@"DYLD_LIBRARY_PATH", [resdir stringByAppendingPathComponent:@"lib"]);
        execv(argv[0], argv);
        _exit(1);
    }
    
    // Set up CHANDLERHOME and CHANDLERBIN as in the script
    if (nil == [env objectForKey:@"CHANDLERHOME"]) {
        SetEnv(@"CHANDLERHOME", resdir);
    }
    if (nil == [env objectForKey:@"CHANDLERBIN"]) {
        SetEnv(@"CHANDLERBIN", resdir);
    }

    // Similarly for PYTHONPATH
    NSArray *pythonPaths =
        [NSArray arrayWithObjects:
            [[resdir stringByAppendingPathComponent:@"release"] stringByAppendingPathComponent:@"site-packages"],
            [resdir stringByAppendingPathComponent:@"parcels"],
            nil
        ];
    SetEnv(@"PYTHONPATH", pythonPaths);

    // Unclear if this "cd" is necessary, but the script does/did it ...    
    [[NSFileManager defaultManager] changeCurrentDirectoryPath:resdir];
#ifdef DEBUG
    Py_VerboseFlag = 1;
#endif
    
    // Now that we have the right DYLD_LIBRARY_PATH and PYTHONPATH set up,
    // we're aiming to invoke the python interpreter programmatically by
    // calling Py_Main.

    // Stash the (C) path to Chandler.py in a main_cpath, so we can
    // hand it off to Py_Main later.
    char main_cpath[MAXPATHLEN+1];

    [mainPath getFileSystemRepresentation:main_cpath maxLength:sizeof(main_cpath)];
    main_cpath[sizeof(main_cpath)-1] = '\0';

    // To support restarting, we will have to ensure that sys.executable
    // in python points at the app binary (i.e. this program, compiled).
    // We'll use PyRun_SimpleString() to pass in the python code to set
    // it before running Chandler.py as the main program.
    
    // First, figure out the path to the compiled binary via
    // -[NSBundle executablePath], and stash it in a char[] buffer.
    char executable_cpath[MAXPATHLEN+1];
    [[bundle executablePath] getFileSystemRepresentation:executable_cpath maxLength:sizeof(executable_cpath)];
    executable_cpath[sizeof(executable_cpath)-1] = '\0';
    
    // Next, store the python code to set sys.executable in a
    // separate buffer, exec_cstring.
    const char EXEC_FORMAT[] = "import sys\nsys.executable=\"%s\"\n";
    char exec_cstring[sizeof(EXEC_FORMAT) + sizeof(executable_cpath)];

    snprintf(exec_cstring, sizeof(exec_cstring) - 1, EXEC_FORMAT, executable_cpath);    
    
    // Done with Foundation stuff
    [pool release];
    
    // Initialize Python
    Py_Initialize();
    
    // Insert "Chandler.py" into the list of arguments
    int i;
    int newArgc = argc + 1;
    char **newArgv = malloc((newArgc + 1) * sizeof(char *));
    
    newArgv[0] = argv[0];
    newArgv[1] = "Chandler.py";
    
    for(i=2; i<= newArgc; i++) {
        newArgv[i] = argv[i-1];
    }

    // Set up sys.executable    
    PyRun_SimpleString(exec_cstring);

    // ... and let Python run Chandler.py as the main program.
    exit(Py_Main(newArgc, newArgv));
    
}