
VERSION=2.3.3
BZIP2VERSION=1.0.2
ZLIBVERSION=1.2.1

include $(BUILD_ROOT)/Makefile.inc

PYTHON=$(BUILD_ROOT)/python
SRC=$(PYTHON)/Python-$(VERSION)

ifeq ($(DEBUG),1)

SUFFIX=_d
CONF_DBG=--with-pydebug --with-suffix=$(SUFFIX)
COMP_OPT=OPT=-g

else

SUFFIX=
CONF_DBG=
COMP_OPT=

endif

ifeq ($(OS),Cygwin)

BINDIR=$(PREFIX)/bin

$(SRC)/PCbuild/pcbuild.sln:
	(cd win32; tar -cf - *.sln *.vcproj) | (cd $(SRC)/PCbuild; tar -xf -)

bzip2-$(BZIP2VERSION)/libbz2.lib:
	cd bzip2-$(BZIP2VERSION); MAKEFLAGS=; \
        nmake -nologo -f makefile.msc

zlib-$(ZLIBVERSION)/zlib.lib:
	cd zlib-$(ZLIBVERSION); MAKEFLAGS=; \
        nmake -nologo -f win32/makefile.msc

build: apply compile install

compile: $(SRC)/PCbuild/pcbuild.sln bzip2-$(BZIP2VERSION)/libbz2.lib zlib-$(ZLIBVERSION)/zlib.lib
	cd $(SRC)/PCbuild; \
        devenv.com pcbuild.sln /build $(Snap)

install:
	mkdir -p $(BINDIR)/DLLs $(BINDIR)/Include $(BINDIR)/Lib $(BINDIR)/libs
	(cd $(SRC)/PCbuild; \
         tar cf - python$(SUFFIX).exe \
                  pythonw$(SUFFIX).exe \
                  python23$(SUFFIX).dll) | \
        (cd $(BINDIR); tar -xvf -)
	(cd $(SRC)/PCbuild; \
         tar cf - python23$(SUFFIX).lib \
                  python23$(SUFFIX).exp) | \
        (cd $(BINDIR)/libs; tar -xvf -)
	(cd $(SRC)/Lib; tar cf - *.py) | (cd $(BINDIR)/Lib; tar -xvf -)
	(cd $(SRC)/PCbuild; tar cf - *.pyd) | (cd $(BINDIR)/DLLs; tar -xvf -)
	for mod in compiler distutils email encodings hotshot xml \
                   bsddb logging; \
        do \
            (cd $(SRC)/Lib; tar cf - `find $$mod -name '*.py'`) | \
            (cd $(BINDIR)/Lib; tar -xvf -); \
        done
	(cd $(SRC)/Include; tar cf - *.h) | (cd $(BINDIR)/Include; tar -xvf -)
	cp -p $(SRC)/PC/pyconfig.h $(BINDIR)/Include

expand: Python-$(VERSION).tgz
	tar xvzf Python-$(VERSION).tgz
	tar xvzf bzip2-$(BZIP2VERSION).tar.gz
	tar xvzf zlib-$(ZLIBVERSION).tar.gz

apply: patches
	patch -Nup0 < patches; echo ok

clean:
	cd $(SRC)/PCbuild; devenv.com pcbuild.sln /clean $(Snap)
	rm -f $(SRC)/PCbuild/pcbuild.sln
	-cd bzip2-$(BZIP2VERSION); MAKEFLAGS=; nmake -f Makefile.msc clean
	-cd zlib-$(ZLIBVERSION); MAKEFLAGS=; nmake -f win32/Makefile.msc clean

snap: 
	cd $(BUILD_ROOT); \
        tar -cvzf $(PYTHON)/$(SNAP).tar.gz \
                  $(SNAP)/bin/python*.* $(SNAP)/bin/libs \
                  $(SNAP)/bin/DLLs $(SNAP)/bin/Include $(SNAP)/bin/Lib \
            -X $(PYTHON)/xcludes

else

BUILD=build_$(SNAP)

ifeq ($(OS),Darwin)

$(SRC)/$(BUILD)/Makefile:
	cd $(SRC); mkdir -p $(BUILD); cd $(BUILD); \
	../configure --prefix=$(PREFIX) $(CONF_DBG) \
                     --enable-framework=$(PREFIX)/Library/Frameworks

build: apply
	cd $(SRC)/$(BUILD); \
        $(MAKE) DB=$(PREFIX)/db $(COMP_OPT) frameworkinstallframework; \
        $(MAKE) DB=$(PREFIX)/db $(COMP_OPT) frameworkinstallapps

snap: 
	cd $(BUILD_ROOT); \
        tar -cvzf $(PYTHON)/$(SNAP).tar.gz \
                  $(SNAP)/Library/Frameworks/Python.framework \
            -X $(PYTHON)/xcludes

expand: Python-$(VERSION).tgz
	tar xvzf Python-$(VERSION).tgz

else

$(SRC)/$(BUILD)/Makefile:
	cd $(SRC); mkdir -p $(BUILD); cd $(BUILD); \
	../configure --prefix=$(PREFIX) $(CONF_DBG)

bzip2-$(BZIP2VERSION)/libbz2.a:
	cd bzip2-$(BZIP2VERSION); \
        make libbz2.a; \
        install -D libbz2.a $(PREFIX)/lib/libbz2.a; \
        install -D bzlib.h $(PREFIX)/include/bzlib.h

build: bzip2-$(BZIP2VERSION)/libbz2.a apply
	cd $(SRC)/$(BUILD); \
	$(MAKE) DB=$(PREFIX)/db $(COMP_OPT) install

snap: 
	cd $(BUILD_ROOT); \
        tar -cvzf $(PYTHON)/$(SNAP).tar.gz \
                  $(SNAP)/bin/idle $(SNAP)/bin/python* \
                  $(SNAP)/lib/python* \
                  $(SNAP)/include/python* \
            -X $(PYTHON)/xcludes

expand: Python-$(VERSION).tgz
	tar xvzf Python-$(VERSION).tgz
	tar xvzf bzip2-$(BZIP2VERSION).tar.gz

endif

apply: $(SRC)/$(BUILD)/Makefile patches
	patch -Nup0 < patches; echo ok

clean:
	cd $(SRC); rm -rf $(BUILD)

endif
