include ../../Makefile.inc

DLLS_DIR=libs

ifeq ($(SNAP),debug)
DLLS=$(DLLS_DIR)/msvcp71d.dll $(DLLS_DIR)/msvcr71d.dll $(DLLS_DIR)/msvcrtd.dll
else
DLLS=$(DLLS_DIR)/msvcp71.dll $(DLLS_DIR)/msvcr71.dll
endif

build:	chandler.exe

chandler.exe: winlaunch/winlaunch.c
	devenv.com launcher.sln /build $(SNAP)
	cp winlaunch/$(Snap)/chandler.exe $(BUILD_ROOT)/$(SNAP)
	cp $(DLLS) $(BUILD_ROOT)/$(SNAP)/bin

clean:
	rm $@ 




