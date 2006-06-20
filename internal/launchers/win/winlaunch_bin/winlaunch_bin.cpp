/* -*- Mode: C++; tab-width: 4; indent-tabs-mode: nil; c-basic-offset: 4 -*- */
/*
 *  Copyright (c) 2003-2006 Open Source Applications Foundation
 *
 *  Licensed under the Apache License, Version 2.0 (the "License");
 *  you may not use this file except in compliance with the License.
 *  You may obtain a copy of the License at
 *
 *      http://www.apache.org/licenses/LICENSE-2.0
 *
 *  Unless required by applicable law or agreed to in writing, software
 *  distributed under the License is distributed on an "AS IS" BASIS,
 *  WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
 *  See the License for the specific language governing permissions and
 *  limitations under the License.
 */

//Turn on Windows XP SP1 APIs
#define _WIN32_WINNT 0x0502

#include <windows.h>
#include <stdlib.h>
#include <assert.h>

#include "atlstr.h"
#include "Python.h"

typedef void (CALLBACK* LPFNSETDLLDIRECTORY)(LPCTSTR);
static LPFNSETDLLDIRECTORY MySetDllDirectory = NULL;

void PathTooLongErrorDialog (LPCSTR  path)
{
    CString  message;

    message.Format (_T("Chandler can't start because the path is too long: "
                       "\"%s\". To fix the problem, "
                       "try reinstalling Chandler into another location."),
                    path);
    MessageBox(NULL, message, _T("Unexpected Error"), MB_OK);
}

void MissingFileOrFolderErrorDialog (LPCSTR  missingFileOrFolder)
{
    CString  message;

    message.Format (_T("Chandler can't start because it can't find a missing "
                       "file or folder (\"%s\"). To fix the problem, "
                       "try reinstalling Chandler."), missingFileOrFolder);
    MessageBox(NULL, message, _T("Unexpected Error"), MB_OK);
}

int APIENTRY WinMain (HINSTANCE hInstance,
                      HINSTANCE hPrevInstance,
                      LPSTR     lpCmdLine,
                      int       nCmdShow)
{
    LPSTR       bufferPtr;
    FILE       *filePtr;
    int         index;
    DWORD       length;
    HMODULE     module;
    CString     path;
    CString     pathToChandler;
    CString     pathToExe;    
    int         result = EXIT_FAILURE;
    BOOL        success;

    /*
     * Get the path to the directory of our executable
     */
    bufferPtr = pathToExe.GetBufferSetLength (_MAX_PATH);
    length = GetModuleFileName (NULL, bufferPtr, _MAX_PATH);
    assert (length);
    pathToExe.ReleaseBuffer();

    /*
     * See if we need to exit because of problems.
     */
    if (!length) return EXIT_FAILURE;
    if (length == _MAX_PATH && GetLastError() == ERROR_INSUFFICIENT_BUFFER) {
        PathTooLongErrorDialog(_T(""));
        return EXIT_FAILURE;
    }
    
    index = pathToExe.ReverseFind (TCHAR ('\\'));
    pathToExe.Truncate (index);
    /*
     * Get the path to the Chandler.py
     */
    pathToChandler = pathToExe;
    index = pathToChandler.ReverseFind (TCHAR ('\\'));
    pathToChandler.Truncate (index);
    index = pathToChandler.ReverseFind (TCHAR ('\\'));
    pathToChandler.Truncate (index);

    #ifndef _DEBUG
        _putenv(_T("PYTHONOPTIMIZE=1"));
    #endif

    /*
     * SetDllDirectory is an entry point defined in XP SP1 that allows
     * us to specify a directory to search first. Check to see if we
     * can use it and give it a tryGoogle says:
     *
     * "No longer is the current directory searched first when loading DLLs!
     * This change was also made in Windows XP SP1. The default behavior now
     * is to look in all the system locations first, then the current directory,
     * and finally any user-defined paths. This will have an impact on your code
     * if you install a DLL in the application's directory because Windows Server
     * 2003 no longer loads the 'local' DLL if a DLL of the same name is in the
     * system directory. A common example is if an application won't run with a
     * specific version of a DLL, an older version is installed that does work
     * in the application directory. This scenario will fail in Windows Server 2003.
     * 
     * The reason this change was made was to mitigate some kinds of trojaning
     * attacks. An attacker may be able to sneak a bad DLL into your application
     * directory or a directory that has files associated with your application.
     * The DLL search order change removes this attack vector.
     *
     * The SetDllDirectory function, also available in Windows XP SP1, modifies
     * the search path used to locate DLLs for the application and affects all
     * subsequent calls to the LoadLibrary and LoadLibraryEx functions by the
     * application."
     * GetExceptionCode() == EXCEPTION_INT_DIVIDE_BY_ZERO ? EXCEPTION_EXECUTE_HANDLER : EXCEPTION_CONTINUE_SEARCH
     */
    module = GetModuleHandle(_T("kernel32.dll"));
    if(module) {
        MySetDllDirectory = LPFNSETDLLDIRECTORY (GetProcAddress (module,
                                                                 #ifdef UNICODE
                                                                     _T("SetDllDirectoryW")
                                                                 #else
                                                                     _T("SetDllDirectoryA")
                                                                 #endif // !UNICODE
                                                                ));
    }

    /* For Windows XP SP1+ / Server 2003 we use SetDllDirectory to avoid dll hell */
    if (MySetDllDirectory) {
        MySetDllDirectory   (pathToExe);
    }
    /*
     * PYTHONCASEOK must be removed because we treat import paths as
     * case sensitive.
     */
    _putenv(_T("PYTHONCASEOK="));
    /*
     * PYTHONHOME must be set because that's what Python
     * uses to to find Lib, the module directory
     */
    path = _T("PYTHONHOME=");
    path += pathToExe;
    _putenv (path);
    /*
     * PYTHONPATH must be set because otherwise Chandler won't find
     * application.
     */
    path = _T("PYTHONPATH=");
    path += pathToChandler;
    _putenv (path);
    /*
     * PATH must be set because some dlls don't get found
     * pre XP SP1
     */
    path = _T("PATH=");
    path += pathToExe;
    _putenv (path);
    /*
     * Current directory is used in the search path for dlls pre XP SP1
     */
    success = SetCurrentDirectory (pathToExe);
    if (!success) {
        MissingFileOrFolderErrorDialog (pathToExe);
    } else {
        /*
         * Pass along the command line arguments to chandler.
         */
        int argc = __argc;
        char ** argv = __argv;

        path = pathToChandler;
        path = path + _T("\\Chandler.py");

	/*
	 * See if we need to exit because of problems.
	 */
        if (path.GetLength() > _MAX_PATH) {
            /*
             * This should not really be possible, but just in case.
             */
            PathTooLongErrorDialog (path);
            return EXIT_FAILURE;
        }

        argv [0] = LPSTR (LPCSTR (path));

        filePtr = fopen (path, "r");
        if (!filePtr) {
            MissingFileOrFolderErrorDialog (path);
        } else {
            Py_Initialize();
            PySys_SetArgv (argc, argv);
            result = PyRun_SimpleFileEx (filePtr, path,
                                         /*close file is */ true);
	    if (result) {
	        result = EXIT_FAILURE;
	    } else {
	        result = EXIT_SUCCESS;
	    }
            /*
             * We don't write out a message when PyRun_SimpleFile returns failure
             * because Chandler is repsponsible for printing errors. There is a
             * rare case in which Chandler is so broken that an error dialog can't
             * be displayed that will result in no indication of failure. -- DJA
             */
            if (result == EXIT_SUCCESS) {
                Py_Finalize();
            }
        }
    }
    return result;
}


