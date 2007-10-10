setlocal
set rootdir=%~dp0
set CHANDLERBIN=%rootdir%\windows
set CHANDLERHOME=%rootdir%\chandler
"%CHANDLERBIN%"\release\RunPython.bat -O "%CHANDLERHOME%"\Chandler.py --profileDir="%rootdir%\profile" --repodir="%rootdir%\windows" --datadir=../../profile/data --logdir=../../profile/logs --force-platform --encrypt %*
endlocal
