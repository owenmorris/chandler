
include ../Makefile.inc

VERSION=1.3.21
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

$(SRC)/$(BUILD)/Makefile:
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

$(SRC)/$(BUILD)/Makefile:
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

snap: 
	cd $(BUILD_ROOT); \
	tar -cvzf $(SWIG)/$(SNAP).tar.gz \
                  $(SNAP)/bin/swig$(EXECUTABLE) \
                  $(SNAP)/share/aclocal/swig.m4 \
                  $(SNAP)/lib/swig1.3 

clean:
	cd $(SRC); rm -rf $(BUILD)

expand: swig-$(VERSION).tar.gz 
	tar xvzf swig-$(VERSION).tar.gz

build: swig

