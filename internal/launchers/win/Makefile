include ../../Makefile.inc

ifeq ($(SNAP),debug)
DLLS=win/msvcp71d.dll win/msvcr71d.dll win/msvcrtd.dll
else
DLLS=win/msvcp71.dll win/msvcr71.dll
endif

build:	chandler.exe

chandler.exe: winlaunch/winlaunch.c
	devenv.com launcher.sln /build $(SNAP)
	cp winlaunch/$(Snap)/chandler.exe $(BUILD_ROOT)/$(SNAP)
	cp $(DLLS) $(BUILD_ROOT)/$(SNAP)/bin

clean:
	rm $@ 




