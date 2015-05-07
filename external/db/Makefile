
VERSION=4.6.21
RELVER=$(VERSION)-$(BRANCH_REV_PREFIX)3
DB=$(BUILD_ROOT)/db
SUBTREE=$(DB)/chandler-bdb
SRC=dummy.txt
TARBALL=db-$(SNAP)-$(RELVER).tar.gz

include $(BUILD_ROOT)/Makefile.inc

ifeq ($(OS),Cygwin)

BUILD=build_windows
BINDIR=$(SUBTREE)/$(BUILD)/$(Snap)

$(SUBTREE)/$(BUILD)/Berkeley_DB.sln:
	(cd win32/$(basename $(VERSION)); tar -cf - *.sln *.vcproj) | (cd $(SUBTREE)/$(BUILD); tar -xf -)

build: compile installext

compile: $(SUBTREE)/$(BUILD)/Berkeley_DB.sln
	cd $(SUBTREE)/$(BUILD); \
        devenv.com Berkeley_DB.sln /project build_all /build "$(Snap) x86"

installext:
	mkdir -p $(PREFIX)/bin/db $(PREFIX)/include/db $(PREFIX)/lib
	(cd $(SUBTREE)/dbinc; tar cf - cxx_*.h) | (cd $(PREFIX)/include/db; tar xvf -)
	(cd $(SUBTREE)/$(BUILD); tar cf - *.h) | (cd $(PREFIX)/include/db; tar xvf -)
	(cd $(BINDIR); tar cf - *.dll) | (cd $(PREFIX)/bin; tar xvf -)
	(cd $(BINDIR); tar cf - *.exe) | (cd $(PREFIX)/bin/db; tar xvf -)
	(cd $(BINDIR); tar cf - *.lib *.exp) | (cd $(PREFIX)/lib; tar xvf -)

clean:
	cd $(SUBTREE)/$(BUILD); \
      devenv.com Berkeley_DB.sln /project build_all /clean "$(Snap) x86"
	rm -f $(SUBTREE)/$(BUILD)/Berkeley_DB.sln
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

$(SUBTREE)/$(BUILD)/Makefile:
	cd $(SUBTREE); mkdir -p $(BUILD); cd $(BUILD); \
      ../dist/configure --prefix=$(PREFIX)/db \
                        --disable-static \
                        --with-pic \
                        $(CONF_DBG)

build: $(SUBTREE)/$(BUILD)/Makefile
	cd $(SUBTREE)/$(BUILD); $(MAKE); $(MAKE) install
	touch dummy.txt

ifneq (/,$(SUBTREE)/$(BUILD))
clean:
	rm -f $(CHANDLERBIN)/$(SNAP)/$(TARBALL).inst
endif

binaries: strip
	tar -C $(BUILD_ROOT) -cvzf $(DB)/$(TARBALL) \
        --exclude '*.a' \
        $(SNAP)/db/bin $(SNAP)/db/lib

endif

install: $(TARBALL)
	cp -p $(TARBALL) $(CHANDLERARCHIVES)
