
VERSION=4.6.21
RELVER=$(VERSION)-$(BRANCH_REV_PREFIX)3
DB=$(BUILD_ROOT)/db
SRC=$(DB)/db-$(VERSION)
TARBALL=db-$(SNAP)-$(RELVER).tar.gz

include $(BUILD_ROOT)/Makefile.inc

ifeq ($(OS),Cygwin)

BUILD=build_windows
BINDIR=$(SRC)/$(BUILD)/$(Snap)

$(SRC)/$(BUILD)/Berkeley_DB.sln:
	(cd win32/$(basename $(VERSION)); tar -cf - *.sln *.vcproj) | (cd $(SRC)/$(BUILD); tar -xf -)

build: expand apply compile installext

compile: $(SRC)/$(BUILD)/Berkeley_DB.sln
	cd $(SRC)/$(BUILD); \
        devenv.com Berkeley_DB.sln /project build_all /build "$(Snap) x86"

installext:
	mkdir -p $(PREFIX)/bin/db $(PREFIX)/include/db $(PREFIX)/lib
	(cd $(SRC)/dbinc; tar cf - cxx_*.h) | (cd $(PREFIX)/include/db; tar xvf -)
	(cd $(SRC)/$(BUILD); tar cf - *.h) | (cd $(PREFIX)/include/db; tar xvf -)
	(cd $(BINDIR); tar cf - *.dll) | (cd $(PREFIX)/bin; tar xvf -)
	(cd $(BINDIR); tar cf - *.exe) | (cd $(PREFIX)/bin/db; tar xvf -)
	(cd $(BINDIR); tar cf - *.lib *.exp) | (cd $(PREFIX)/lib; tar xvf -)

clean:
	cd $(SRC)/$(BUILD); \
      devenv.com Berkeley_DB.sln /project build_all /clean "$(Snap) x86"
	rm -f $(SRC)/$(BUILD)/Berkeley_DB.sln
	rm -f $(CHANDLERBIN)/$(SNAP)/$(TARBALL).inst

# do not remove the cd $(BUILD_ROOT); and try to replace 
# it with a -C $(BUILD_ROOT) -- this will fail because the
# shell will expand the wildcards *before* tar will change
# the directory.  I (bear) have now made this mistake 3 times
# with the last one getting into the source tree
binaries: strip
	cd $(BUILD_ROOT); tar -cvzf $(DB)/$(TARBALL) \
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

ifneq (/,$(SRC)/$(BUILD))
clean:
	rm -rf $(SRC)/$(BUILD)
	rm -f $(CHANDLERBIN)/$(SNAP)/$(TARBALL).inst
endif

binaries: strip
	tar -C $(BUILD_ROOT) -cvzf $(DB)/$(TARBALL) \
        --exclude '*.a' \
        $(SNAP)/db/bin $(SNAP)/db/lib

endif

apply: expand patches-$(VERSION)
	cd $(SRC); patch -Np0 < $(DB)/patch-11547.txt; echo ok
	patch -Nup0 < patches-$(VERSION); echo ok

db-$(VERSION).tar.gz:
	$(CURL) http://builds.osafoundation.org/external/db-$(VERSION).tar.gz

sources: db-$(VERSION).tar.gz

db-$(VERSION)-expanded: db-$(VERSION).tar.gz
	tar -xvzf db-$(VERSION).tar.gz
	touch db-$(VERSION)-expanded

expand: db-$(VERSION)-expanded

install: $(TARBALL)
	cp -p $(TARBALL) $(CHANDLERARCHIVES)
