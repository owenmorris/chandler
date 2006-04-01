
include ../Makefile.inc

VERSION=5.0
RELVER=$(VERSION)-$(BRANCH_REV_PREFIX)3
BUILD=build_$(SNAP)
READLINE=$(BUILD_ROOT)/readline
SRC=$(READLINE)/$(BUILD)
SRC_BUILD=$(SRC)/readline-$(VERSION)
TARBALL=readline-$(SNAP)-$(RELVER).tar.gz

.PHONY: readline

ifeq ($(OS),Darwin)

$(SRC)/Makefile:
	cd $(SRC_BUILD); \
  ./configure --prefix=$(PREFIX)

readline: $(SRC)/Makefile apply
	$(MAKE) -C $(SRC_BUILD)
	$(MAKE) -C $(SRC_BUILD) install

ifneq (/,$(READLINE)/$(BUILD))
clean:
	rm -rf $(READLINE)/$(BUILD)
	rm -f $(READLINE)/readline-$(VERSION)-$(SNAP)-expanded
endif

ifeq ($(OS_MAJOR_VER),8)
apply:
	mv $(SRC_BUILD)/shlib/Makefile $(SRC_BUILD)/shlib/Makefile.backup
	sed -e 's/ -dynamic/ -dynamiclib/' $(SRC_BUILD)/shlib/Makefile.backup > $(SRC_BUILD)/shlib/Makefile
else
# Nothing to do
apply:
endif 

binaries:
	cd $(BUILD_ROOT); \
    tar -cvzf $(READLINE)/$(TARBALL) \
          $(SNAP)/lib/libreadline*.dylib \
          --exclude '*.a'

install: $(TARBALL)
	cp -p $(TARBALL) $(CHANDLERARCHIVES)

readline-$(VERSION).tar.gz:
	$(CURL) http://builds.osafoundation.org/external/readline-$(VERSION).tar.gz 

sources: readline-$(VERSION).tar.gz

readline-$(VERSION)-$(SNAP)-expanded: readline-$(VERSION).tar.gz
	mkdir -p $(READLINE)/$(BUILD)
	tar -C $(READLINE)/$(BUILD) -xzf $(READLINE)/readline-$(VERSION).tar.gz
	touch $(READLINE)/readline-$(VERSION)-$(SNAP)-expanded

expand: readline-$(VERSION)-$(SNAP)-expanded

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

build: expand readline

