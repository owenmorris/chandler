
VERSION=1.2
PATHAN=$(BUILD_ROOT)/persistence/pathan
XERCESC=$(BUILD_ROOT)/persistence/xerces-c/xerces-c-src2_4_0
SRC=$(PATHAN)/libpathan-$(VERSION)

include $(BUILD_ROOT)/Makefile.inc

ifeq ($(DEBUG),1)
CONF_DBG=--compiletype=debug
else
CONF_DBG=
endif

ifeq ($(OS),Cygwin)

$(SRC)/Win32Projects/Pathan/Pathan.sln:
	(cd win32; tar cf - *.sln *.vcproj) | \
        (cd $(SRC)/Win32Projects/Pathan; tar xf -)

compile: $(SRC)/Win32Projects/Pathan/Pathan.sln
	cd $(SRC); \
        export XERCESCROOT=`cygpath -aw $(XERCESC)`; \
	devenv.com Win32Projects/Pathan/Pathan.sln \
                   /project PathanDll /build $(Snap)

install:
	mkdir -p $(PREFIX)/include/pathan
	(cd $(SRC)/src/dom3-xpath; \
         tar cf - `find . -name '*.hpp' -print`) | \
        (cd $(PREFIX)/include/pathan; tar xvf - )
	install $(SRC)/src/config/win32/config.h $(PREFIX)/include/pathan
	(cd $(SRC)/lib; tar -cf - *.dll) | (cd $(PREFIX)/bin; tar xvf - )
	(cd $(SRC)/lib; tar -cf - *.lib *.exp) | (cd $(PREFIX)/lib; tar xvf - )

build: compile install

clean:
	cd $(SRC); \
        export XERCESCROOT=`cygpath -aw $(XERCESC)`; \
	devenv.com Win32Projects/Pathan/Pathan.sln \
                   /project PathanDll /clean $(Snap)
	rm -f $(SRC)/Win32Projects/Pathan/Pathan.sln

snap: 
	cd $(BUILD_ROOT); \
        tar -cvzf $(PATHAN)/$(SNAP).tar.gz $(SNAP)/bin/Pathan*.dll

else

BUILD=build_$(SNAP)


$(SRC)/$(BUILD)/Makefile.defs:
	cd $(SRC); mkdir -p $(BUILD); cd $(BUILD); \
        (cd $(SRC); tar -cf - autotools examples src util \
                              aclocal.m4 configure configure.in \
                              Makefile Makefile.defs.in Makefile.deps \
                              Makefile.plat runConfigure) | tar -xf - ; \
        XERCESCROOT=$(XERCESC)/$(BUILD) \
	./runConfigure --prefix=$(PREFIX) $(CONF_DBG)

build: $(SRC)/$(BUILD)/Makefile.defs
	cd $(SRC)/$(BUILD); \
	XERCESCROOT=$(XERCESC)/$(BUILD) $(MAKE); \
	XERCESCROOT=$(XERCESC)/$(BUILD) $(MAKE) install

snap: 
	cd $(BUILD_ROOT); \
        tar -cvzf $(PATHAN)/$(SNAP).tar.gz $(SNAP)/lib/libpathan*

clean:
	cd $(SRC); rm -rf $(BUILD)

endif

expand: libpathan-$(VERSION)-2-src.tar.gz
	tar xvzf libpathan-$(VERSION)-2-src.tar.gz

