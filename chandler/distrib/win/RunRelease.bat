@ECHO OFF
setlocal
cd ..\Chandler
set PATH=..\release\bin
..\release\bin\python -O Chandler.py $*
endlocal
