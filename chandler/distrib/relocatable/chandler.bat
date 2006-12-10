setlocal
set rootdir=%~dp0
set CHANDLERBIN=%rootdir%\windows
set CHANDLERHOME=%rootdir%\chandler
"%CHANDLERBIN%"\release\RunChandler.bat --profileDir="%rootdir%\profile" --repodir="%rootdir%\windows" --datadir=../../profile/data --logdir=../../profile/logs --encrypt %*
endlocal
