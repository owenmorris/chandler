
include ../Makefile.inc

VERSION=20Feb04
SWIG=$(BUILD_ROOT)/swig
SRC=$(SWIG)/SWIG-$(VERSION)

ifeq ($(DEBUG),1)
CONF_OPT=--enable-debug
DIST_OPT=--debug
FINAL=0
SUFFIX=d
else
CONF_OPT=--enable-optimized
DIST_OPT=
FINAL=1
SUFFIX=
endif


BUILD=build_$(SNAP)

.PHONY: swig


ifeq ($(OS),Cygwin)

EXECUTABLE=.exe

swig:  $(SRC)/$(BUILD)/Makefile
	cd $(SRC)/$(BUILD); \
	$(MAKE) ; \
	$(MAKE) install

$(SRC)/$(BUILD)/Makefile: apply
	cd $(SRC); \
	mkdir -p $(BUILD); \
	cd $(BUILD); \
	../configure --prefix=$(PREFIX) $(CONF_OPT) \
	--build=i386-pc-cygwin \
	--with-python=$(PYTHON) \
	--without-ruby \
	--without-php4 \
	--without-chicken \
	--without-pike \
	--without-guile \
	--without-ocaml

else

EXECUTABLE=

$(SRC)/$(BUILD)/Makefile: apply
	cd $(SRC); \
	mkdir -p $(BUILD); \
	cd $(BUILD); \
	../configure --prefix=$(PREFIX) $(CONF_OPT) \
                 --enable-shared \
                 --with-python=$(PYTHON) \
                 --without-ruby \
                 --without-php4 \
                 --without-chicken \
                 --without-pike \
                 --without-guile \
                 --without-ocaml

swig:   $(SRC)/$(BUILD)/Makefile
	cd $(SRC)/$(BUILD); \
        $(MAKE) ; \
        $(MAKE) install 

endif

apply: patches-$(VERSION)
	patch -Nup0 < patches-$(VERSION); echo ok

# snap target can be empty since we don't actually need swig when
# running Chandler
snap: 

clean:
	cd $(SRC); rm -rf $(BUILD)

expand: SWIG-$(VERSION).tar.gz 
	tar xvzf SWIG-$(VERSION).tar.gz

build: swig

