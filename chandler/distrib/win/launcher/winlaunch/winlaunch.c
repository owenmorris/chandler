
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

	int argc = 1;
	char *name = "Chandler";
	char **argv = &name;

    /* MessageBox(NULL, "Loading Chandler!", "", MB_OK); */
	Py_SetProgramName("Chandler");
	Py_Initialize();
	PySys_SetArgv(argc,argv);
	fp = fopen("Chandler.py", "r+");
	retval = PyRun_SimpleFile(fp, "Chandler.py");
	/*
	if(retval){
		MessageBox(NULL, "Boo!", "", MB_OK);
	}else{
		MessageBox(NULL, "Yeah!", "", MB_OK);
	}
	*/

	Py_Exit(0);
	/*NOTREACHED*/
}
