include ../../Makefile.inc

DLLS_DIR=libs

ifeq ($(SNAP),debug)

DLLS=$(DLLS_DIR)/msvcp71d.dll $(DLLS_DIR)/msvcr71d.dll $(DLLS_DIR)/msvcrtd.dll

build:	winlaunch2/chandlerDebug.exe winlaunch1/chandler.exe

winlaunch2/chandlerDebug.exe: winlaunch2/winlaunch2.cpp
	devenv.com winlaunch2/winlaunch2.sln /build $(SNAP)
	cp winlaunch2/$(Snap)/chandlerDebug.exe $(BUILD_ROOT)

winlaunch1/chandler.exe: winlaunch1/winlaunch1.cpp
	devenv.com winlaunch1/winlaunch1.sln /build $(SNAP)
	cp winlaunch1/$(Snap)/chandler.exe $(BUILD_ROOT)/$(SNAP)/bin
	cp $(DLLS) $(BUILD_ROOT)/$(SNAP)/bin

else

DLLS=$(DLLS_DIR)/msvcp71.dll $(DLLS_DIR)/msvcr71.dll

build:	winlaunch2/chandler.exe winlaunch1/chandler.exe

winlaunch2/chandler.exe: winlaunch2/winlaunch2.cpp
	devenv.com winlaunch2/winlaunch2.sln /build $(SNAP)
	cp winlaunch2/$(Snap)/chandler.exe $(BUILD_ROOT)

winlaunch1/chandler.exe: winlaunch1/winlaunch1.cpp
	devenv.com winlaunch1/winlaunch1.sln /build $(SNAP)
	cp winlaunch1/$(Snap)/chandler.exe $(BUILD_ROOT)/$(SNAP)/bin
	cp $(DLLS) $(BUILD_ROOT)/$(SNAP)/bin

clean:
	rm $@ 

endif



