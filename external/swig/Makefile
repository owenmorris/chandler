
include ../Makefile.inc

VERSION=1.3.29
SWIG=$(BUILD_ROOT)/swig
SRC=$(SWIG)/swig-$(VERSION)
TARBALL=

BUILD=build_$(SNAP)

.PHONY: swig

ifeq ($(OS),Cygwin)

$(SRC)/SWIG13.sln:
	tar -C win32 --exclude .svn -cf - . | tar -C $(SRC) -xvf -

swig: $(SRC)/SWIG13.sln
	cd $(SRC); devenv.com SWIG13.sln /build Release
	mkdir -p $(PREFIX)/bin/swig
	tar -C $(SRC) -cf - SWIG.exe Lib | tar -C $(PREFIX)/bin/swig -xvf -

clean:
	cd $(SRC); devenv.com SWIG13.sln /clean Release; echo ok

else

$(SRC)/$(BUILD)/Makefile:
	mkdir -p $(SRC)/$(BUILD)
	cd $(SRC)/$(BUILD); ../configure --prefix=$(PREFIX)

swig: $(SRC)/$(BUILD)/Makefile
	$(MAKE) -C $(SRC)/$(BUILD)
	$(MAKE) -C $(SRC)/$(BUILD) install

ifneq (/,$(SRC)/$(BUILD))
clean:
	rm -rf $(SRC)/$(BUILD)
endif

endif

apply: patches-$(VERSION)
	patch -Nup0 < patches-$(VERSION); echo ok

# Nothing to do
binaries:

# Nothing to do
upload:

# Nothing to do
install:

swig-$(VERSION).tar.gz:
	$(CURL) http://builds.osafoundation.org/external/swig-$(VERSION).tar.gz 

sources: swig-$(VERSION).tar.gz

swig-$(VERSION)-expanded: swig-$(VERSION).tar.gz
	tar xvzf swig-$(VERSION).tar.gz
	touch swig-$(VERSION)-expanded

expand: swig-$(VERSION)-expanded

build: expand apply swig

