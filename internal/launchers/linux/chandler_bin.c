/* chandler_bin.c
 *
__version__ = "$Revision$"
__date__ = "$Date$"
__copyright__ = "Copyright (c) 2003 Open Source Applications Foundation"
__license__ = "http://osafoundation.org/Chandler_0.1_license_terms.htm"
 *
 */

#include <stdlib.h>
#include "Python.h"

main(int argc, char **argv)
{
    int retval = 0;
    FILE *fp;
    struct stat statBuf;            /* For lstat() */
    chdir("..");
    if((lstat("Chandler.py", &statBuf)==-1) || ! S_ISREG(statBuf.st_mode)) {
        printf("ERROR: Chandler.py not found; exiting\n");
        exit(-1);
    }

    Py_SetProgramName(argv[0]);
    Py_Initialize();
    PySys_SetArgv(argc, argv);


    fp = fopen("Chandler.py", "r+");
    retval = PyRun_SimpleFile(fp, "Chandler.py");
    if(retval != 0) {
        printf("Python interpreter exited with value = %d\n", retval);
    }

    Py_Exit(0);
    /*NOTREACHED*/
}
