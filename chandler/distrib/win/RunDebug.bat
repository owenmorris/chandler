@ECHO OFF
cd ..\Chandler
set PATHBAK=%PATH%
set PATH=..\debug\bin
..\debug\bin\python Chandler.py
set PATH=%PATHBAK%
