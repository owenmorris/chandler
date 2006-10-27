
BUILD=build_$(SNAP)
READLINE=$(BUILD_ROOT)/readline

include ../Makefile.inc

ifeq ($(OS),Cygwin)
    VERSION=1.7
else
    VERSION=5.1
endif

SRC=$(READLINE)/$(BUILD)
SRC_BUILD=$(SRC)/readline-$(VERSION)
RELVER=$(VERSION)-$(BRANCH_REV_PREFIX)2
TARBALL=readline-$(SNAP)-$(RELVER).tar.gz

.PHONY: readline

ifeq ($(OS),Darwin)

$(SRC_BUILD)/Makefile:
	cd $(SRC_BUILD); ./configure --prefix=$(PREFIX)

readline: apply $(SRC_BUILD)/Makefile
	$(MAKE) -C $(SRC_BUILD)
	$(MAKE) -C $(SRC_BUILD) install

ifneq (/,$(READLINE)/$(BUILD))
clean:
	rm -rf $(READLINE)/$(BUILD)
	rm -f $(READLINE)/readline-$(VERSION)-$(SNAP)-expanded
	rm -f $(CHANDLERBIN)/$(SNAP)/$(TARBALL).inst
endif

binaries:
	cd $(BUILD_ROOT); \
        tar -cvzf $(READLINE)/$(TARBALL) $(SNAP)/lib/libreadline*.dylib \
            --exclude '*.a'

install: $(TARBALL)
	cp -p $(TARBALL) $(CHANDLERARCHIVES)

readline-$(VERSION).tar.gz:
	$(CURL) http://builds.osafoundation.org/external/readline-$(VERSION).tar.gz 
	$(CURL) http://builds.osafoundation.org/external/readline51-001
	$(CURL) http://builds.osafoundation.org/external/readline51-002
	$(CURL) http://builds.osafoundation.org/external/readline51-003
	$(CURL) http://builds.osafoundation.org/external/readline51-004

sources: readline-$(VERSION).tar.gz

readline-$(VERSION)-$(SNAP)-expanded: readline-$(VERSION).tar.gz
	mkdir -p $(READLINE)/$(BUILD)
	tar -C $(READLINE)/$(BUILD) -xzf $(READLINE)/readline-$(VERSION).tar.gz
	touch $(READLINE)/readline-$(VERSION)-$(SNAP)-expanded

expand: readline-$(VERSION)-$(SNAP)-expanded

apply: expand
	cd $(READLINE)/$(BUILD)/readline-$(VERSION); \
        cat $(READLINE)/readline51* | patch -N; \
        echo ok

else
ifeq ($(OS),Cygwin)

readline: expand
	cd $(READLINE)/$(BUILD)/Readline-$(VERSION); \
      $(PYTHON) setup.py build --build-base=$(BUILD) $(DIST_OPT) install

ifneq (/,$(READLINE)/$(BUILD))
clean:
	rm -rf $(READLINE)/$(BUILD)
	rm -f $(READLINE)/readline-$(VERSION)-$(SNAP)-expanded
	rm -f $(CHANDLERBIN)/$(SNAP)/$(TARBALL).inst
endif

binaries:
	cd $(BUILD_ROOT); \
        tar -cvzf $(READLINE)/$(TARBALL) $(SNAP)/$(SITE)/readline.py $(SNAP)/$(SITE)/_rlsetup.pyd

install: $(TARBALL)
	cp -p $(TARBALL) $(CHANDLERARCHIVES)

Readline-$(VERSION).zip:
	$(CURL) http://builds.osafoundation.org/external/Readline-$(VERSION).zip

sources: Readline-$(VERSION).zip

Readline-$(VERSION)-$(SNAP)-expanded: Readline-$(VERSION).zip
	mkdir -p $(READLINE)/$(BUILD)
	unzip $(READLINE)/Readline-$(VERSION).zip -d $(READLINE)/$(BUILD)
	touch Readline-$(VERSION)-$(SNAP)-expanded

expand: Readline-$(VERSION)-$(SNAP)-expanded

else

  # Nothing to do
readline:

  # Nothing to do
clean:

  # Nothing to do
binaries:

  # Nothing to do
sources:

  # Nothing to do
expand:

  # Nothing to do
install:

endif
endif

build: readline
