
include ../Makefile.inc

VERSION=2.5
RELVER=$(VERSION)-2
SRC=$(INTERNAL)/wxPython-$(VERSION)

ifeq ($(DEBUG),1)
CONF_OPT=--enable-debug
DIST_OPT=--debug
FINAL=0
SUFFIX=d
else
CONF_OPT=--enable-optimized
DIST_OPT=
FINAL=1
SUFFIX=
endif



BUILD=build_$(SNAP)

.PHONY: wxWidgets wxPython


ifeq ($(OS),Cygwin)

wxWidgets:
	cd $(SRC); \
        export WXWIN=`cygpath -aw $(SRC)`; MAKEFLAGS=; \
	devenv.com build/msw/msw.sln /build $(Snap)
	mkdir -p $(PREFIX)/$(SITE)/wx
	install $(SRC)/lib/vc_dll/*251$(SUFFIX)*_vc.dll $(PREFIX)/$(SITE)/wx

wxPython:
	cd $(SRC)/wxPython; \
        export WXWIN=`cygpath -aw $(SRC)`; MAKEFLAGS=; \
	$(PYTHON) setup.py BUILD_BASE=$(BUILD) \
                           build $(DIST_OPT) \
                           install \
                           FINAL=$(FINAL) HYBRID=0

MANIFEST=$(SNAP)/$(SITE)/wx

clean:
	cd $(SRC); devenv.com build/msw/msw.sln /clean $(Snap)
	cd $(SRC)/wxPython; rm -rf $(SRC)/wxPython/$(BUILD)

else

ifeq ($(OS),Darwin)

$(SRC)/$(BUILD)/Makefile:
	cd $(SRC); mkdir -p $(BUILD); cd $(BUILD); \
	../configure --prefix=$(PREFIX) $(CONF_OPT) \
                     --disable-monolithic \
                     --enable-geometry \
                     --enable-sound \
                     --with-sdl \
                     --enable-display \
                     --with-libpng=builtin \
                     --with-mac \
                     --with-opengl

wxPython:
	cd $(SRC)/wxPython; \
        $(PYTHON) setup.py BUILD_OGL=0 BUILD_GLCANVAS=0 \
                           BUILD_BASE=$(BUILD) \
                           WX_CONFIG=$(PREFIX)/bin/wx-config \
                           build $(DIST_OPT) install FINAL=$(FINAL)

MANIFEST=$(SNAP)/$(SITE)/wx \
         $(SNAP)/$(SITE)/wxPython \
	 $(SNAP)/lib/libwx_mac* \
	 $(SNAP)/lib/libwx_base_carbon* \
	 $(SNAP)/share/locale

else

$(SRC)/$(BUILD)/Makefile:
	cd $(SRC); mkdir -p $(BUILD); cd $(BUILD); \
	../configure --prefix=$(PREFIX) $(CONF_OPT) \
                     --disable-monolithic \
                     --enable-geometry \
                     --enable-sound \
                     --with-sdl \
                     --enable-display \
                     --with-libpng=builtin \
                     --with-gtk \
                     --enable-gtk2 \
                     --enable-unicode

wxPython:
	cd $(SRC)/wxPython; \
        $(PYTHON) setup.py BUILD_OGL=0 BUILD_GLCANVAS=0 \
                           BUILD_BASE=$(BUILD) \
                           WX_CONFIG=$(PREFIX)/bin/wx-config \
                           WXPORT=gtk2 UNICODE=1 \
                           build $(DIST_OPT) install FINAL=$(FINAL)

MANIFEST=$(SNAP)/$(SITE)/wx \
         $(SNAP)/$(SITE)/wxPython \
	 $(SNAP)/lib/libwx_base* \
	 $(SNAP)/lib/libwx_gtk2* \
	 $(SNAP)/share/locale

endif

wxWidgets: $(SRC)/$(BUILD)/Makefile
	$(MAKE) -C $(SRC)/$(BUILD)
	$(MAKE) -C $(SRC)/$(BUILD)/contrib/src/gizmos
	$(MAKE) -C $(SRC)/$(BUILD)/contrib/src/ogl \
                CXXFLAGS="-DwxUSE_DEPRECATED=0"
	$(MAKE) -C $(SRC)/$(BUILD)/contrib/src/stc
	$(MAKE) -C $(SRC)/$(BUILD)/contrib/src/xrc
	$(MAKE) -C $(SRC)/$(BUILD) install
	$(MAKE) -C $(SRC)/$(BUILD)/contrib/src/gizmos install
	$(MAKE) -C $(SRC)/$(BUILD)/contrib/src/ogl install
	$(MAKE) -C $(SRC)/$(BUILD)/contrib/src/stc install
	$(MAKE) -C $(SRC)/$(BUILD)/contrib/src/xrc install

clean:
	cd $(SRC); rm -rf $(BUILD); \
	cd $(SRC)/wxPython; rm -rf $(BUILD)

endif

build: wxWidgets wxPython

upload: wxPython-$(SNAP)-$(RELVER).tar.gz
	scp wxPython-$(SNAP)-$(RELVER).tar.gz $(UPLOAD)

snap: 
	cd $(BUILD_ROOT); \
	tar -cvzf $(SRC)/wxPython-$(SNAP)-$(RELVER).tar.gz $(MANIFEST)

install:
	cd $(BUILD_ROOT); \
	tar -cf - $(MANIFEST) | tar -C $(BUILD_ROOT)/../chandler -xvf -
