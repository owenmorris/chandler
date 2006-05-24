
include ../Makefile.inc

VERSION=5.1
RELVER=$(VERSION)-$(BRANCH_REV_PREFIX)1
BUILD=build_$(SNAP)
READLINE=$(BUILD_ROOT)/readline
SRC=$(READLINE)/$(BUILD)
SRC_BUILD=$(SRC)/readline-$(VERSION)
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

build: readline
