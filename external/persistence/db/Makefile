
VERSION=4.4.16
RELVER=$(VERSION)-$(BRANCH_REV_PREFIX)2
DB=$(BUILD_ROOT)/persistence/db
SRC=$(DB)/db-$(VERSION)

include $(BUILD_ROOT)/Makefile.inc

ifeq ($(OS),Cygwin)

BUILD=build_win32
BINDIR=$(SRC)/$(BUILD)/$(Snap)

$(SRC)/$(BUILD)/Berkeley_DB.sln:
	(cd win32/$(basename $(VERSION)); tar -cf - *.sln *.vcproj) | (cd $(SRC)/$(BUILD); tar -xf -)

build: expand apply compile installext

compile: $(SRC)/$(BUILD)/Berkeley_DB.sln
	cd $(SRC)/$(BUILD); \
        devenv.com Berkeley_DB.sln /project build_all /build $(Snap)

installext:
	mkdir -p $(PREFIX)/bin/db $(PREFIX)/include/db $(PREFIX)/lib
	(cd $(SRC)/dbinc; tar cf - cxx_*.h) | (cd $(PREFIX)/include/db; tar xvf -)
	(cd $(SRC)/$(BUILD); tar cf - *.h) | (cd $(PREFIX)/include/db; tar xvf -)
	(cd $(BINDIR); tar cf - *.dll) | (cd $(PREFIX)/bin; tar xvf -)
	(cd $(BINDIR); tar cf - *.exe) | (cd $(PREFIX)/bin/db; tar xvf -)
	(cd $(BINDIR); tar cf - *.lib *.exp) | (cd $(PREFIX)/lib; tar xvf -)

clean:
	cd $(SRC)/$(BUILD); \
      devenv.com Berkeley_DB.sln /project build_all /clean $(Snap)
	rm -f $(SRC)/$(BUILD)/Berkeley_DB.sln

binaries: 
	cd $(BUILD_ROOT); tar -cvzf $(DB)/db-$(SNAP)-$(RELVER).tar.gz \
                                    $(SNAP)/bin/libdb*.dll \
                                    $(SNAP)/bin/db/db_*.exe

else

ifeq ($(DEBUG),1)
CONF_DBG=--enable-debug
else
CONF_DBG=
endif


BUILD=build_$(SNAP)

$(SRC)/$(BUILD)/Makefile:
	cd $(SRC); mkdir -p $(BUILD); cd $(BUILD); \
      ../dist/configure --prefix=$(PREFIX)/db \
                        --disable-static \
                        --with-pic \
                        $(CONF_DBG)

build: expand apply $(SRC)/$(BUILD)/Makefile
	cd $(SRC)/$(BUILD); $(MAKE); $(MAKE) install

clean:
	cd $(SRC); rm -rf $(BUILD)

binaries:
	cd $(BUILD_ROOT); tar -cvzf $(DB)/db-$(SNAP)-$(RELVER).tar.gz \
                              --exclude '*.a'                         \
                              $(SNAP)/db/bin $(SNAP)/db/lib

endif

apply: expand patches-$(VERSION)
	patch -Nup0 < patches-$(VERSION); echo ok

db-$(VERSION).tar.gz:
	$(CURL) http://builds.osafoundation.org/external/db-$(VERSION).tar.gz

sources: db-$(VERSION).tar.gz

db-$(VERSION)-expanded: db-$(VERSION).tar.gz
	tar -xvzf db-$(VERSION).tar.gz
	touch db-$(VERSION)-expanded

expand: db-$(VERSION)-expanded

upload: db-$(SNAP)-$(RELVER).tar.gz
	scp db-$(SNAP)-$(RELVER).tar.gz $(UPLOAD)

install: db-$(SNAP)-$(RELVER).tar.gz
	tar -C $(CHANDLERBIN) -xzf db-$(SNAP)-$(RELVER).tar.gz
