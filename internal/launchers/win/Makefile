include ../../Makefile.inc

build:	chandler.exe

chandler.exe: winlaunch/winlaunch.c
	devenv.com launcher.sln /build $(SNAP)
	cp winlaunch/$(Snap)/chandler.exe $(BUILD_ROOT)/$(SNAP)

clean:
	rm $@ 




