/* -*- Mode: C++; tab-width: 4; indent-tabs-mode: nil; c-basic-offset: 4 -*- */
/* chandler.c
 *
__version__ = "$Revision$"
__date__ = "$Date$"
__copyright__ = "Copyright (c) 2003-2004 Open Source Applications Foundation"
__license__ = "http://osafoundation.org/Chandler_0.1_license_terms.htm"
 *
 */

#include <string.h>
#include <libgen.h>
#include <stdlib.h>
#include <limits.h>
#include <unistd.h>
#include <sys/stat.h>

char * AbsolutePath(char *base, char *rel) {

    /* Given a base directory and a path (possibly) relative to that base,
     * return the malloc'd absolute path of that relative path.  If rel begins
     * with a slash, then it is already absolute (but we'll run it through
     * realpath() anyway to clean it up).
     */

    char *pathBuf = malloc((PATH_MAX+1) * sizeof(char));
    char *retPath = NULL;
    char *slashPtr = strchr(rel, '/');
    if (!pathBuf) {
      printf("ERROR: Out of memory!\n");
      exit(-1);
    }
    if(slashPtr == rel){
        /* rel begins with a slash -- it's already absolute */
        return realpath(rel, pathBuf);
    }
    retPath = malloc((strlen(base)+strlen(rel)+2) * sizeof(char));
    if (!retPath) {
      printf("ERROR: Out of memory!\n");
      exit(-1);
    }
    strcpy(retPath, base);
    strcat(retPath, "/");
    strcat(retPath, rel);
    return realpath(retPath, pathBuf);
}


char * FindProgram(char *arg) {

    /* Given what was passed to this program as argv[0], determine the
     * actual path to the program.  The steps are:
     *
     *   1. If there is a slash in arg, then it is either an absolute or
     *      relative path already, and so it should get run through
     *      realpath() to follow symlinks and remove "." and "..".
     *   2. Otherwise traverse the list of directories from the PATH
     *      environment variable, appending arg to each directory and
     *      looking for a match.
     *
     * Returns a pointer to a malloc'd buffer containing the program's
     * actual path, or NULL if it could not be determined, although I
     * can't think of a case where it couldn't be determined...
     */

    char cwd[PATH_MAX];             /* For the call to getcwd() */
    char *envPath = NULL;           /* For the call to getenv() */
    char *pathList = NULL;          /* A copy of envPath for strtok() */
    char *pathDir = NULL;           /* For each dir in pathList */
    char *realPath = NULL;          /* The answer */
    struct stat statBuf;            /* For lstat() */

    char *slashPtr = strchr(arg, '/');
    if(slashPtr){ /* slash indicates it's either relative or absolute */
        getcwd(cwd, PATH_MAX);
        realPath = AbsolutePath(cwd, arg);
    } else {
        envPath = getenv("PATH");
        pathList = malloc((strlen(envPath)+1) * sizeof(char));
        if (!pathList) {
            printf("ERROR: Out of memory!\n");
            exit(-1);
        }
        strcpy(pathList,envPath); /* copy because strtok is destructive */
        while(pathDir=strtok(pathList,":")){
            pathList = NULL;  /* strtok needs this to be NULL after 1st time */
            if(realPath) free(realPath); /* in case we've allocated one */
            realPath = AbsolutePath(pathDir, arg);
            if(realPath && (lstat(realPath, &statBuf)!=-1) &&
             (statBuf.st_mode & S_IFREG)) {
                /* file exists and it is a regular file */
                /*
                printf("Found a match within the path:  %s\n", pathDir);
                */
                break;
            }
        }
    }
    return realPath;
}


int PrependToLdLibraryPath(char *dir){

    /* Given a directory, prepend it to the existing LD_LIBRARY_PATH 
     * environment variable.
     */

    char *newLibraryPath;
    char *curLibraryPath = getenv("LD_LIBRARY_PATH");
    if(curLibraryPath) {
        newLibraryPath = malloc((strlen(dir) + strlen(curLibraryPath) + 2) * sizeof(char));
        if (!newLibraryPath) {
          printf("ERROR: Out of memory!\n");
          exit(-1);
        }
        strcpy(newLibraryPath, dir);
        strcat(newLibraryPath, ":");
        strcat(newLibraryPath, curLibraryPath);
        return setenv("LD_LIBRARY_PATH", newLibraryPath, 1);
    } else{
        return setenv("LD_LIBRARY_PATH", dir, 1);
    }
}

#ifndef DEBUGMODE
#define SNAP "/release"
#else
#define SNAP "/debug"
#endif

#define APPENDLIB1 SNAP "/lib"
#define APPENDLIB2 SNAP "/db/lib"
#define APPENDLIB3 SNAP "/dbxml/lib"
#define PROG_BIN   "chandler_bin"

char *LibDir(char *exeDir, char *appendLib)
{
    struct stat statBuf;            /* For lstat() */
    char *libDir = malloc((strlen(exeDir)+strlen(appendLib)+1) * sizeof(char));
    if (!libDir) {
      printf("ERROR: Out of memory!\n");
      exit(-1);
    }
    strcpy(libDir, exeDir);
    strcat(libDir, appendLib);
    if((lstat(libDir, &statBuf)==-1) || ! S_ISDIR(statBuf.st_mode)) {
        printf("ERROR: %s is not a directory; exiting\n", libDir);
        exit(-1);
    }
    return libDir;
}

main(int argc, char **argv)
{
    int retVal = 0;
    pid_t pid;
    int status, died;
    struct stat statBuf;            /* For lstat() */

    char *exePath = NULL;
    char *exeDir = NULL;
    char *libDir1 = NULL;
    char *libDir2 = NULL;
    char *libDir3 = NULL;

    char *chandlerHome;

    exePath = FindProgram(argv[0]);
    exeDir = dirname(exePath);

    libDir1 = LibDir(exeDir, APPENDLIB1);
    libDir2 = LibDir(exeDir, APPENDLIB2);
    libDir3 = LibDir(exeDir, APPENDLIB3);

    printf("exePath:  [%s]\n", exePath);
    printf("exeDir :  [%s]\n", exeDir);
    printf("libDir1:  [%s]\n", libDir1);
    printf("libDir2:  [%s]\n", libDir2);
    printf("libDir3:  [%s]\n", libDir3);
    PrependToLdLibraryPath(libDir1);
    PrependToLdLibraryPath(libDir2);
    PrependToLdLibraryPath(libDir3);

    chandlerHome = AbsolutePath(exeDir, ".");
    setenv("PYTHONPATH", chandlerHome, 1);
    free(chandlerHome);

    unsetenv("PYTHONHOME");
#ifndef DEBUGMODE
    setenv("PYTHONOPTIMIZE", "1", 1);
#endif
    chdir(exeDir);
    free(exePath);
    exePath = malloc((strlen(libDir1)+strlen(PROG_BIN)+2) * sizeof(char));
    if (!exePath) {
      printf("ERROR: Out of memory!\n");
      exit(-1);
    }
    strcpy(exePath, libDir1);
    strcat(exePath, "/");
    strcat(exePath, PROG_BIN);
    if((lstat(exePath, &statBuf)==-1) || ! S_ISREG(statBuf.st_mode)) {
        printf("ERROR: %s is not a file; exiting\n", exePath);
        exit(-1);
    }

    free(libDir1);
    free(libDir2);
    free(libDir3);

    switch(pid=fork()){
        case -1:
            printf("Can't fork\n");
            exit(-1);
        case 0:
            /* printf("I'm the child\n"); */
            retVal = execv(exePath, argv);
        default:
            died = wait(&status);
            /* printf("Parent, status=%d, died=%d\n", status, died); */
    }
    /* printf("%d\n", retVal); */
}
