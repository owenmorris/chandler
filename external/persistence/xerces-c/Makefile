
VERSION=2_4_0
XERCESC=$(BUILD_ROOT)/persistence/xerces-c
SRC=$(XERCESC)/xerces-c-src$(VERSION)

include $(BUILD_ROOT)/Makefile.inc

ifeq ($(DEBUG),1)
CONF_DBG=-d
else
CONF_DBG=
endif

ifeq ($(OS),Cygwin)

sln:
	(cd win32; tar -cf - *.sln `find . -name '*.vcproj' -print`) | \
        (cd $(SRC)/Projects/Win32/VC7/xerces-all; tar -xf -)

compile: sln
	cd $(SRC); \
        export XERCESCROOT=$(SRC); \
	devenv.com Projects/Win32/VC7/xerces-all/xerces-all.sln \
                   /project XercesLib /build $(Snap)

install:
	mkdir -p $(PREFIX)/include
	(cd $(SRC)/src; \
         tar -cf - `find . \( -name '*.hpp' -o -name '*.c' \) -print`) | \
        (cd $(PREFIX)/include; tar xvf - )
	(cd $(SRC)/Build/Win32/VC7/$(Snap); tar -cf - *.dll) | \
        (cd $(PREFIX)/bin; tar xvf - )
	(cd $(SRC)/Build/Win32/VC7/$(Snap); tar -cf - *.lib *.exp) | \
        (cd $(PREFIX)/lib; tar xvf - )
        

build: compile install

clean:
	cd $(SRC); \
        export XERCESCROOT=$(SRC); \
	devenv.com Projects/Win32/VC7/xerces-all/xerces-all.sln \
                   /project XercesLib /clean $(Snap)

snap: 
	cd $(BUILD_ROOT); \
        tar -cvzf $(XERCESC)/$(SNAP).tar.gz $(SNAP)/bin/xerces*.dll

else

ifeq ($(OS),Darwin)
CONF_OS=-pmacosx
else
CONF_OS=-plinux
endif

BUILD=build_$(SNAP)


$(SRC)/$(BUILD)/src/xercesc/Makefile:
	cd $(SRC); mkdir -p $(BUILD); cd $(BUILD); \
        ( cd $(SRC); tar -cf - obj src version.incl ) | tar -xf - ; \
        cd src/xercesc; \
        XERCESCROOT=$(SRC)/$(BUILD) \
	./runConfigure $(CONF_OS) $(CONF_DBG) -P$(PREFIX) \
                       -minmem -nsocket -tnative -rnone

build: $(SRC)/$(BUILD)/src/xercesc/Makefile
	cd $(SRC)/$(BUILD)/src/xercesc; \
	XERCESCROOT=$(SRC)/$(BUILD) $(MAKE); \
	rm -f $(PREFIX)/lib/libxerces*; \
	XERCESCROOT=$(SRC)/$(BUILD) $(MAKE) install

snap: 
	cd $(BUILD_ROOT); \
        tar -cvzf $(XERCESC)/$(SNAP).tar.gz $(SNAP)/lib/libxerces*

clean:
	cd $(SRC); rm -rf $(BUILD)

endif

expand: xerces-c-src$(VERSION).tar.gz
	tar xvzf xerces-c-src$(VERSION).tar.gz
