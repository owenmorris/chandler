
#include <windows.h>
#include "Python.h"

int WINAPI WinMain(
    HINSTANCE hInstance,      /* handle to current instance */
    HINSTANCE hPrevInstance,  /* handle to previous instance */
    LPSTR lpCmdLine,          /* pointer to command line */
    int nCmdShow              /* show state of window */
)
{
	int retval = 0;
	FILE *fp;

#ifndef _DEBUG
	_putenv("PYTHONOPTIMIZE=1");
#endif
	Py_SetProgramName("Chandler");
	Py_Initialize();
	PySys_SetArgv(__argc,__argv);
	fp = fopen("Chandler.py", "r+");
	retval = PyRun_SimpleFile(fp, "Chandler.py");
	if(retval){
		MessageBox(NULL, "Failed to run Chandler.py", "", MB_OK);
	}
	Py_Exit(0);
	/*NOTREACHED*/
}
