#!/usr/bin/env python
# vi:ts=2 sw=2 nofen

__author__       = "Mike Taylor <bear@code-bear.com>"
__contributors__ = []
__copyright__    = "Copyright (c) 2005 Open Source Applications Foundation"
__version__      = "1.0"
__svn__          = "$Id$"
  
    # 
    # Designed to run every 15-30 minutes
    #
    # This program scans the continuous directories for the very latest entries
    # updates the QA working directory with the newest files.
    #
    # The builds are created with the datetime of the build as part of the filename
    # and this is hindering the auto-download scripts that QA needs to run.  So this
    # program copies the latest builds into a known directory and renames the builds
    # to a simple name that QA can trust will always be present.
    #
    # Assumptions:
    #                            
    # source tree:
    #    /home/builder/www/chandler/continuous
    #        + ( osx | win | linux )
    #            + YYYYMMDDHHMMSS 
    #
    # target tree:
    #    /home/builder/www/chandler/continuous/qa
    #
    # each build will be present in qa named as:
    #                   
    #     Chandler_osx.dmg
    #     Chandler_win.exe
    #     Chandler_win.zip
    #     Chandler_linux.i386.rpm
    #     Chandler_linux.tar.gz
    #

import os, glob, string

workingDirectory = '/home/builder/www/docs/chandler/continuous'
platforms        = ['osx', 'win', 'linux']
        
def main():
    os.chdir(workingDirectory)
                     
    targetDir = os.path.join(workingDirectory, 'qa')
                                
    if not os.path.isdir(targetDir):
        os.mkdir(targetDir)
        
    platformDirs = []
    
    for platform in platforms:
        platformDirs += glob.glob(platform)

    for platformDirectory in platformDirs:
        source = os.path.join(workingDirectory, platformDirectory)
        
        if os.path.isdir(source):
            os.chdir(source)
            
            sourceDirs = glob.glob('[0-9]*')
            
            sourceDirs.sort()
        
            if len(sourceDirs) > 0:
                sourceDir = sourceDirs[-1]
                buildDate = sourceDir
                sourceDir = os.path.join(source, sourceDir)

                for item in os.listdir(sourceDir):
                    if item[:9] == 'Chandler_':
                        target = item.replace('_' + buildDate, '')
                        targetFile = os.path.join(targetDir, target)                      
                                                          
                        if os.path.islink(targetFile):
                            os.unlink(targetFile) 
                                
                        os.symlink(os.path.join(sourceDir, item), targetFile)

main()
