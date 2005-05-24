
VERSION=3.2
RELVER=$(VERSION)-1
ICU=$(BUILD_ROOT)/icu
SRC=$(ICU)/icu-$(VERSION)

include $(BUILD_ROOT)/Makefile.inc

BUILD=$(SRC)/build_$(SNAP)

ifeq ($(OS),Cygwin)

build: expand compile installext

compile:
	mkdir -p $(BUILD)/lib $(BUILD)/bin $(BUILD)/exe
	cd $(SRC)/icu/source/allinone; MAKEFLAGS=; \
        devenv.com allinone.sln /build $(Snap)
	tar -C $(SRC)/icu/lib -cf - . | tar -C $(BUILD)/lib -xvf -
	(cd $(SRC)/icu/bin; tar -cf - *.exe) | tar -C $(BUILD)/exe -xvf -
	(cd $(SRC)/icu/bin; tar -cf - *.dll) | tar -C $(BUILD)/bin -xvf -
	rm -f $(SRC)/icu/lib/* $(SRC)/icu/bin/*

installext:
	mkdir -p $(PREFIX)/bin/icu $(PREFIX)/include/icu $(PREFIX)/lib
	tar -C $(SRC)/icu/include -cf - . | tar -C $(PREFIX)/include/icu -xvf -
	tar -C $(BUILD)/lib -cf - . | tar -C $(PREFIX)/lib -xvf -
	tar -C $(BUILD)/bin -cf - . | tar -C $(PREFIX)/bin -xvf -
	tar -C $(BUILD)/exe -cf - . | tar -C $(PREFIX)/bin/icu -xvf -

clean:
	rm -rf $(BUILD)
	cd $(SRC)/icu/source/allinone; MAKEFLAGS=; \
        devenv.com allinone.sln /clean $(Snap)

snap: 
	cd $(BUILD_ROOT); \
        tar -cvzf $(ICU)/icu-$(SNAP)-$(RELVER).tar.gz \
                  $(SNAP)/bin/icu*.dll \
                  $(SNAP)/bin/icu/*.exe; \
	$(MD5) $(ICU)/icu-$(SNAP)-$(RELVER).tar.gz > $(ICU)/icu-$(SNAP)-$(RELVER).tar.gz.md5

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

$(BUILD)/Makefile:
	mkdir -p $(BUILD)
	cd $(BUILD); \
	$(SRC)/icu/source/runConfigureICU \
            $(CONF_RUN) --prefix=$(PREFIX)/icu $(CONF_DBG)

build: expand $(BUILD)/Makefile
	cd $(BUILD); $(MAKE); $(MAKE) install

clean:
	rm -rf $(BUILD)

snap:
	cd $(BUILD_ROOT); \
        tar -cvzf $(ICU)/icu-$(SNAP)-$(RELVER).tar.gz \
		$(SNAP)/icu/bin $(SNAP)/icu/lib; \
	$(MD5) $(ICU)/icu-$(SNAP)-$(RELVER).tar.gz > $(ICU)/icu-$(SNAP)-$(RELVER).tar.gz.md5

endif

icu-$(VERSION).tgz:
	$(CURL) http://builds.osafoundation.org/external/icu-$(VERSION).tgz
	$(CURL) http://builds.osafoundation.org/external/icu-$(VERSION).tgz.md5

#      $(MD5CHECK) icu-$(VERSION).tgz.md5

sources: icu-$(VERSION).tgz

icu-$(VERSION)-expanded: icu-$(VERSION).tgz
	mkdir -p $(ICU)/icu-$(VERSION)
	tar -C $(ICU)/icu-$(VERSION) -xvzf icu-$(VERSION).tgz
	touch icu-$(VERSION)-expanded

expand: icu-$(VERSION)-expanded

upload: icu-$(SNAP)-$(RELVER).tar.gz
	scp icu-$(SNAP)-$(RELVER).tar.gz $(UPLOAD)
	scp icu-$(SNAP)-$(RELVER).tar.gz.md5 $(UPLOAD)

install: icu-$(SNAP)-$(RELVER).tar.gz
	tar -C $(CHANDLERBIN) -xvzf icu-$(SNAP)-$(RELVER).tar.gz
