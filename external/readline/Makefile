
VERSION=5.2
RELVER=$(VERSION)-$(BRANCH_REV_PREFIX)2
READLINE=$(BUILD_ROOT)/readline
SRC=$(READLINE)/readline-$(VERSION)
TARBALL=readline-$(SNAP)-$(RELVER).tar.gz

include $(BUILD_ROOT)/Makefile.inc

ifeq ($(OS),Darwin)

BUILD=build_$(SNAP)

$(SRC)/$(BUILD)/Makefile: expand apply
	mkdir -p $(SRC)/$(BUILD)
	cd $(SRC)/$(BUILD); ../configure --prefix=$(PREFIX)

build: $(SRC)/$(BUILD)/Makefile
	$(MAKE) -C $(SRC)/$(BUILD)
	$(MAKE) -C $(SRC)/$(BUILD) install

apply: patches-$(VERSION)-$(OS)
	patch -Nup0 < $< ; echo ok

ifneq (/,$(SRC)/$(BUILD))
clean:
	rm -rf $(SRC)/$(BUILD)
	rm -f $(CHANDLERBIN)/$(SNAP)/$(TARBALL).inst
endif

binaries:
	cd $(BUILD_ROOT); \
        tar -cvzf $(READLINE)/$(TARBALL) $(SNAP)/lib/libreadline*.dylib

install: $(TARBALL)
	cp -p $(TARBALL) $(CHANDLERARCHIVES)

readline-$(VERSION).tar.gz:
	$(CURL) http://builds.osafoundation.org/external/readline-$(VERSION).tar.gz 

sources: readline-$(VERSION).tar.gz

readline-$(VERSION)-expanded: readline-$(VERSION).tar.gz
	tar -xvzf $<
	touch $@

expand: readline-$(VERSION)-expanded

else

ifeq ($(OS),Cygwin)

BUILD=src/readline/$(VERSION)/readline-$(VERSION)

ifeq ($(DEBUG),1)
_SUFFIX=D
else
_SUFFIX=
endif

readline-$(VERSION)-20061112-src.zip:
	$(CURL) http://builds.osafoundation.org/external/$@

sources: readline-$(VERSION)-20061112-src.zip

readline-$(VERSION)-expanded: readline-$(VERSION)-20061112-src.zip
	mkdir -p $(SRC)
	cd $(SRC); unzip $(READLINE)/$<
	touch $@

expand: readline-$(VERSION)-expanded

build: expand
	(cd win32/$(VERSION); tar -cf - *.sln *.vcproj) | tar -C $(SRC)/$(BUILD)/msvc -xvf -
	cd $(SRC)/$(BUILD)/msvc; devenv.com readline.sln /project readline /build $(Snap)
	mkdir -p $(SRC)/lib $(SRC)/include/readline
	cp -p $(SRC)/$(BUILD)/lib/readline$(_SUFFIX).lib $(SRC)/lib
	cp -p $(SRC)/$(BUILD)-src/*.h $(SRC)/include/readline

binaries:

install:

$(TARBALL):
	@echo nothing to do

upload:
	@echo nothing to do

else

  # Nothing to do
build:

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
