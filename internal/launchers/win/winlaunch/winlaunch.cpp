/* -*- Mode: C++; tab-width: 4; indent-tabs-mode: nil; c-basic-offset: 4 -*- */
/*
 *  Copyright (c) 2003-2007 Open Source Applications Foundation
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

#include <windows.h>
#include <assert.h>
#include <process.h>


#include "atlstr.h"

#ifdef _DEBUG
    #define LAUNCHER _T("\\debug\\bin\\pythonw_d.exe")
#else
    #define LAUNCHER _T("\\release\\bin\\pythonw.exe")
#endif

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
    LPSTR               bufferPtr;
    CString             commandLine;
    int                 index;
    DWORD               length;
    CString             pathToPython;
    CString             chandlerHome;
    CString             pathToExe;
    PROCESS_INFORMATION processInfo;
    STARTUPINFO         startupInfo;
    BOOL                success;

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

    index = pathToExe.ReverseFind(TCHAR('\\'));
    pathToExe.Truncate(index);
    /*
     * Get the path to the python launcher
     */
    pathToPython = pathToExe + _T(LAUNCHER);

    /*
     * See if we need to exit because of problems.
     */
    if (pathToPython.GetLength() > _MAX_PATH) {
        PathTooLongErrorDialog (pathToPython);
        return EXIT_FAILURE;
    }

    /*
     * now, get the path to the python launcher's dir
     */
    pathToExe = pathToExe + _T(LAUNCHER);
    index = pathToExe.ReverseFind(TCHAR('\\'));
    pathToExe.Truncate(index);

    /*
     * Get CHANDLERHOME
     */
    chandlerHome = pathToExe;
    index = chandlerHome.ReverseFind(TCHAR('\\'));
    chandlerHome.Truncate(index);
    index = chandlerHome.ReverseFind(TCHAR('\\'));
    chandlerHome.Truncate(index);

    /*
     * PYTHONCASEOK must be removed because we treat import paths as
     * case sensitive.
     */
    _putenv(_T("PYTHONCASEOK="));

    /*
     * PYTHONPATH must be set because otherwise Chandler won't find
     * the application.
     */
    _putenv(_T("PYTHONPATH=") + \
            chandlerHome + _T(";") + \
            chandlerHome + _T("\\parcels"));

    /*
     * PATH must be set because some DLLs don't get found
     * pre XP SP1
     */
    _putenv(_T("PATH=") + pathToExe);

    /*
     * CHANDLERHOME must be set because otherwise Chandler won't be
     * able to install plugins.
     */
    _putenv(_T("CHANDLERHOME=") + chandlerHome);

    /*
     * Current directory is used in the search path for dlls pre XP SP1
     */
    success = SetCurrentDirectory(pathToExe);
    if (!success)
        MissingFileOrFolderErrorDialog(pathToExe);

    /*
     * Wrap the exe path in quotes in case the path contains spaces,
     * so that we get the right number of arguments.
     */
    commandLine = _T("\"") + pathToPython + _T("\" ");
#ifndef _DEBUG
    commandLine += _T("-O ");
#endif
    commandLine += _T("\"") + chandlerHome + _T("\\Chandler.py\" ");
    commandLine += lpCmdLine;

    GetStartupInfo (&startupInfo);
    startupInfo.dwFlags &= ~STARTF_USESHOWWINDOW;

    success = CreateProcess (pathToPython,                  // Path to executable
                             LPSTR (LPCSTR (commandLine)),  // command line
                             NULL,                          // Default process security attributes
                             NULL,                          // Default thread security attributes
                             true,                          // inherit handles from the parent
                             0,                             // Normal priority
                             NULL,                          // Use the same environment as the parent
                             LPSTR (LPCSTR (chandlerHome)), // Launch in the chandlerHome directory
                             &startupInfo,                  // Startup Information
                             &processInfo);                 // Process information stored upon return
    if (!success) {
        int error = GetLastError();
        CString  message;

        message.Format (_T("Chandler couldn't be started because of an "
                           "unexpected problem "
                           "(launching \"%s\" failed, error code %d). "
                           "To fix the problem, "
                           "try reinstalling Chandler."),
                        pathToPython, error);
        MessageBox(NULL, message, _T("Unexpected Error"), MB_OK);
    }

    return EXIT_SUCCESS;
}
