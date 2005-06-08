
#include <windows.h>
#include <assert.h>
#include <process.h>


#include "atlstr.h"

#ifdef _DEBUG
	#define LAUNCHER _T("\\debug\\bin\\chandler.exe")
#else
	#define LAUNCHER _T("\\release\\bin\\chandler.exe")
#endif

int APIENTRY WinMain (HINSTANCE hInstance,
                      HINSTANCE hPrevInstance,
                      LPSTR     lpCmdLine,
                      int       nCmdShow)
{
    LPSTR       		bufferPtr;
    CString     		commandLine;
    int         		index;
    DWORD       		length;
    CString     		pathToChandler;
    CString				pathToExe;
    PROCESS_INFORMATION	processInfo;
    STARTUPINFO			startupInfo;
    BOOL				success;

    /*
     * Get the path to the directory of our executable
     */
    bufferPtr = pathToExe.GetBufferSetLength (_MAX_PATH);
    length = GetModuleFileName (NULL, bufferPtr, _MAX_PATH);
    assert (length);
    pathToExe.ReleaseBuffer();
    
    index = pathToExe.ReverseFind (TCHAR ('\\'));
    pathToExe.Truncate (index);
    /*
     * Get the path to the chandler launcher
     */
    pathToChandler = pathToExe + _T(LAUNCHER);

	commandLine = pathToChandler + _T(" ") + lpCmdLine;

	GetStartupInfo (&startupInfo);
	startupInfo.dwFlags &= ~STARTF_USESHOWWINDOW;

	success = CreateProcess (pathToChandler,		// Path to executable
							 LPSTR (LPCSTR (commandLine)),	// command line
							 NULL,					// Default process security attributes
							 NULL,					// Default thread security attributes
							 true,					// inherit handles from the parent
							 0,						// Normal priority
							 NULL,					// Use the same environment as the parent
							 NULL,					// Launch in the current directory
							 &startupInfo,			// Startup Information
							 &processInfo);			// Process information stored upon return
	if (!success) {
		int error = GetLastError();
		CString  message;

		message.Format (_T("Chandler couldn't be started because of an unexpected problem "
						"(launching \"%s\" failed). To fix the problem, "
						"try reinstalling Chandler."), pathToChandler);
		MessageBox(NULL, message, _T("Unexpected Error"), MB_OK);
	}

	return 0;
}