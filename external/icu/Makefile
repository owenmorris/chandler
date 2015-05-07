
VERSION=55_1
RELVER=$(VERSION)-$(BRANCH_REV_PREFIX)2
ICU=$(BUILD_ROOT)/icu
SRC=$(ICU)/icu-$(VERSION)
BUILD=build_$(SNAP)
TARBALL=icu-$(SNAP)-$(RELVER).tar.gz

include $(BUILD_ROOT)/Makefile.inc

ifeq ($(OS),Cygwin)

build: expand compile installext

compile:
	mkdir -p $(SRC)/$(BUILD)/lib $(SRC)/$(BUILD)/bin $(SRC)/$(BUILD)/exe
	cd $(SRC)/icu/source/allinone; MAKEFLAGS=; \
        devenv.com allinone.sln /build $(Snap)
	tar -C $(SRC)/icu/lib -cf - . | tar -C $(SRC)/$(BUILD)/lib -xvf -
	(cd $(SRC)/icu/bin; tar -cf - *.exe) | tar -C $(SRC)/$(BUILD)/exe -xvf -
	(cd $(SRC)/icu/bin; tar -cf - *.dll) | tar -C $(SRC)/$(BUILD)/bin -xvf -
	rm -f $(SRC)/icu/lib/* $(SRC)/icu/bin/*

installext:
	mkdir -p $(PREFIX)/bin/icu $(PREFIX)/include/icu $(PREFIX)/lib
	tar -C $(SRC)/icu/include -cf - . | tar -C $(PREFIX)/include/icu -xvf -
	tar -C $(SRC)/$(BUILD)/lib -cf - . | tar -C $(PREFIX)/lib -xvf -
	tar -C $(SRC)/$(BUILD)/bin -cf - . | tar -C $(PREFIX)/bin -xvf -
	tar -C $(SRC)/$(BUILD)/exe -cf - . | tar -C $(PREFIX)/bin/icu -xvf -

clean:
	rm -rf $(SRC)/$(BUILD)
	cd $(SRC)/icu/source/allinone; MAKEFLAGS=; \
        devenv.com allinone.sln /clean $(Snap)
	rm -f $(CHANDLERBIN)/$(SNAP)/$(TARBALL).inst

binaries: strip
	cd $(BUILD_ROOT); \
      tar -cvzf $(ICU)/$(TARBALL) \
          $(SNAP)/bin/icu*.dll \
          $(SNAP)/bin/icu/*.exe

else

ifeq ($(DEBUG),1)
CONF_DBG=--enable-debug
else
CONF_DBG=
endif

ifeq ($(OS),Darwin)
CONF_RUN=MacOSX
endif

ifeq ($(OS),Linux)
CONF_RUN=LinuxRedHat
endif

$(SRC)/$(BUILD)/Makefile:
	mkdir -p $(SRC)/$(BUILD)
	cd $(SRC)/$(BUILD); \
      $(SRC)/icu/source/runConfigureICU \
          $(CONF_RUN) --prefix=$(PREFIX)/icu $(CONF_DBG)

build: expand $(SRC)/$(BUILD)/Makefile
	$(MAKE) -C $(SRC)/$(BUILD)
	$(MAKE) -C $(SRC)/$(BUILD) install

ifneq (/,$(SRC)/$(BUILD))
clean:
	rm -rf $(SRC)/$(BUILD)
	rm -f $(CHANDLERBIN)/$(SNAP)/$(TARBALL).inst
endif

binaries: strip
	cd $(BUILD_ROOT); \
      tar -cvzf $(ICU)/$(TARBALL) \
          $(SNAP)/icu/bin $(SNAP)/icu/lib

endif

icu4c-$(VERSION)-src.tgz:
	$(CURL) http://download.icu-project.org/files/icu4c/55.1/icu4c-55_1-src.tgz

sources: icu4c-$(VERSION)-src.tgz

icu-$(VERSION)-src-expanded: icu4c-$(VERSION)-src.tgz
	mkdir -p $(ICU)/icu-$(VERSION)
	tar -C $(ICU)/icu-$(VERSION) -xvzf icu4c-$(VERSION)-src.tgz
	touch icu-$(VERSION)-expanded

expand: icu-$(VERSION)-expanded

install: $(TARBALL)
	cp -p $(TARBALL) $(CHANDLERARCHIVES)

