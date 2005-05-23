
VERSION=3.2
RELVER=$(VERSION)-1
ICU=$(BUILD_ROOT)/icu
SRC=$(ICU)/icu-$(VERSION)

include $(BUILD_ROOT)/Makefile.inc

BUILD=$(SRC)/build_$(SNAP)

ifeq ($(OS),Cygwin)

build: expand compile installext

compile:
	cd $(BUILD); \
        devenv.com `cygpath -aw $(SRC)/icu/source/allinone/allinone.sln` /project /build $(Snap)

installext:
	mkdir -p $(PREFIX)/bin/icu $(PREFIX)/include/db $(PREFIX)/lib
	(cd $(SRC)/dbinc; tar cf - cxx_*.h) | (cd $(PREFIX)/include/db; tar xvf -)
	(cd $(SRC)/$(BUILD); tar cf - *.h) | (cd $(PREFIX)/include/db; tar xvf -)
	(cd $(BINDIR); tar cf - *.dll) | (cd $(PREFIX)/bin; tar xvf -)
	(cd $(BINDIR); tar cf - *.exe) | (cd $(PREFIX)/bin/db; tar xvf -)
	(cd $(BINDIR); tar cf - *.lib *.exp) | (cd $(PREFIX)/lib; tar xvf -)

clean:
	cd $(SRC)/$(BUILD); \
        devenv.com Berkeley_DB.sln /project build_all /clean $(Snap)
	rm -f $(SRC)/$(BUILD)/Berkeley_DB.sln

snap: 
	cd $(BUILD_ROOT); \
        tar -cvzf $(ICU)/icu-$(SNAP)-$(RELVER).tar.gz \
                  $(SNAP)/bin/libdb*.dll \
                  $(SNAP)/bin/db/db_*.exe; \
	$(MD5) $(DB)/db-$(SNAP)-$(RELVER).tar.gz > $(DB)/db-$(SNAP)-$(RELVER).tar.gz.md5

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
