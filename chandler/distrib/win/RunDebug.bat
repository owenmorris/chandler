@ECHO OFF
cd ..\Chandler
set PATHBAK=%PATH%
set PATH=..\debug\bin
..\debug\bin\python_d Chandler.py
set PATH=%PATHBAK%
