
include ../Makefile.inc

VERSION=1.3.24
SWIG=$(BUILD_ROOT)/swig
SRC=$(SWIG)/SWIG-$(VERSION)

BUILD=build_$(SNAP)

.PHONY: swig

ifeq ($(OS),Cygwin)

$(SRC)/SWIG13.sln:
	sed -e "s/1.3.24/$(VERSION)/" win32/Source/Include/swigconfig0.h > win32/Source/Include/swigconfig.h
	tar -C win32 --exclude CVS -cf - . | tar -C $(SRC) -xvf -

swig: $(SRC)/SWIG13.sln
	cd $(SRC); devenv.com SWIG13.sln /build Release
	mkdir -p $(PREFIX)/bin/swig
	tar -C $(SRC) -cf - SWIG.exe Lib | tar -C $(PREFIX)/bin/swig -xvf -

clean:
	cd $(SRC); devenv.com SWIG13.sln /clean Release; echo ok

else

$(SRC)/$(BUILD)/Makefile:
	mkdir -p $(SRC)/$(BUILD); \
	cd $(SRC)/$(BUILD); \
	../configure --prefix=$(PREFIX) \
                     --with-python=$(PYTHON)

swig: $(SRC)/$(BUILD)/Makefile
	$(MAKE) -C $(SRC)/$(BUILD)
	$(MAKE) -C $(SRC)/$(BUILD) install

clean:
	rm -rf $(SRC)/$(BUILD)

endif


apply: patches-$(VERSION)
	patch -Nup0 < patches-$(VERSION); echo ok

# Nothing to do
snap:

# Nothing to do
upload:

# Nothing to do
install:

SWIG-$(VERSION).tar.gz:
	$(CURL) http://builds.o11n.org/external/SWIG-$(VERSION).tar.gz 
	$(CURL) http://builds.o11n.org/external/SWIG-$(VERSION).tar.gz.md5

sources: SWIG-$(VERSION).tar.gz

SWIG-$(VERSION)-expanded: SWIG-$(VERSION).tar.gz
	tar xvzf SWIG-$(VERSION).tar.gz
	touch SWIG-$(VERSION)-expanded

expand: SWIG-$(VERSION)-expanded

build: expand apply swig

