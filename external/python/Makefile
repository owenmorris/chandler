
VERSION=2.3.3
RELVER=$(VERSION)-1
BZIP2VERSION=1.0.2
ZLIBVERSION=1.2.1

include $(BUILD_ROOT)/Makefile.inc

PYTHON=$(BUILD_ROOT)/python
SRC=$(PYTHON)/Python-$(VERSION)

BUILD=build_$(SNAP)

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


ifeq ($(DEBUG),1)
MKBZIP2MF=sed -e "s/ -MD -Ox / -MDd -Zi /" makefile.msc > $(BUILD)/makefile$(SUFFIX).msc
MKZLIBMF=sed -e "s/ -MD -O2 / -MDd -Zi /" win32/makefile.msc > $(BUILD)/win32/makefile$(SUFFIX).msc
else
MKBZIP2MF=echo ok
MKZLIBMF=echo ok
endif


bzip2-$(BZIP2VERSION)/$(BUILD)/makefile$(SUFFIX).msc:
	cd bzip2-$(BZIP2VERSION)/; \
	mkdir $(BUILD); \
	cp *.* words1 $(BUILD)/; \
	$(MKBZIP2MF)

bzip2-$(BZIP2VERSION)/libbz2$(SUFFIX).lib: bzip2-$(BZIP2VERSION)/$(BUILD)/makefile$(SUFFIX).msc
	cd bzip2-$(BZIP2VERSION)/$(BUILD); \
	MAKEFLAGS=; \
        nmake -nologo -f makefile$(SUFFIX).msc; \
	cp libbz2.lib ../libbz2$(SUFFIX).lib

bzip2: bzip2-$(BZIP2VERSION)/libbz2$(SUFFIX).lib


zlib-$(ZLIBVERSION)/$(BUILD)/win32/makefile$(SUFFIX).msc:
	cd zlib-$(ZLIBVERSION)/; \
	mkdir $(BUILD); \
	cp -r *.c *.h win32 $(BUILD)/; \
	$(MKZLIBMF)

zlib-$(ZLIBVERSION)/zlib$(SUFFIX).lib: zlib-$(ZLIBVERSION)/$(BUILD)/win32/makefile$(SUFFIX).msc
	cd zlib-$(ZLIBVERSION)/$(BUILD); \
	MAKEFLAGS=; \
	nmake -nologo -f win32/makefile$(SUFFIX).msc; \
	cp zlib.lib ../zlib$(SUFFIX).lib

zlib: zlib-$(ZLIBVERSION)/zlib$(SUFFIX).lib


build: expand apply compile installext
	mkdir -p $(BUILD_ROOT)/$(SNAP)/$(SITE)

compile: $(SRC)/PCbuild/pcbuild.sln bzip2 zlib
	cd $(SRC)/PCbuild; \
        devenv.com pcbuild.sln /build $(Snap)

installext:
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

Python-$(VERSION).tgz:
	$(CURL) http://builds.o11n.org/external/Python-$(VERSION).tgz
	$(CURL) http://builds.o11n.org/external/Python-$(VERSION).tgz.md5

bzip2-$(BZIP2VERSION).tar.gz:
	$(CURL) http://builds.o11n.org/external/bzip2-$(BZIP2VERSION).tar.gz
	$(CURL) http://builds.o11n.org/external/bzip2-$(BZIP2VERSION).tar.gz.md5

zlib-$(ZLIBVERSION).tar.gz:
	$(CURL) http://builds.o11n.org/external/zlib-$(ZLIBVERSION).tar.gz
	$(CURL) http://builds.o11n.org/external/zlib-$(ZLIBVERSION).tar.gz.md5

sources: Python-$(VERSION).tgz bzip2-$(BZIP2VERSION).tar.gz zlib-$(ZLIBVERSION).tar.gz

Python-$(VERSION)-expanded: Python-$(VERSION).tgz
	tar xvzf Python-$(VERSION).tgz
	touch Python-$(VERSION)-expanded

bzip2-$(BZIP2VERSION)-expanded: bzip2-$(BZIP2VERSION).tar.gz
	tar xvzf bzip2-$(BZIP2VERSION).tar.gz
	touch bzip2-$(BZIP2VERSION)-expanded

zlib-$(ZLIBVERSION)-expanded: zlib-$(ZLIBVERSION).tar.gz
	tar xvzf zlib-$(ZLIBVERSION).tar.gz
	touch zlib-$(ZLIBVERSION)-expanded

expand: Python-$(VERSION)-expanded bzip2-$(BZIP2VERSION)-expanded zlib-$(ZLIBVERSION)-expanded

apply: patches
	patch -Nup0 < patches; echo ok

clean:
	rm -fr bzip2-$(BZIP2VERSION)/$(BUILD) bzip2-$(BZIP2VERSION)/libbz2$(SUFFIX).lib
	rm -fr zlib-$(ZLIBVERSION)/$(BUILD) zlib-$(ZLIBVERSION)/zlib$(SUFFIX).lib
	cd $(SRC)/PCbuild; devenv.com pcbuild.sln /clean $(Snap) || true
	rm -f $(SRC)/PCbuild/pcbuild.sln

snap: 
	cd $(BUILD_ROOT); \
        tar -cvzf $(PYTHON)/python-$(SNAP)-$(RELVER).tar.gz \
                  $(SNAP)/bin/python*.* $(SNAP)/bin/libs \
                  $(SNAP)/bin/DLLs $(SNAP)/bin/Include $(SNAP)/bin/Lib \
            --exclude site-packages \
            --exclude test; \
	$(MD5) $(PYTHON)/python-$(SNAP)-$(RELVER).tar.gz > $(PYTHON)/python-$(SNAP)-$(RELVER).tar.gz.md5

else

ifeq ($(OS),Darwin)

$(SRC)/$(BUILD)/Makefile:
	cd $(SRC); mkdir -p $(BUILD); cd $(BUILD); \
	../configure --prefix=$(PREFIX) $(CONF_DBG) \
                     --enable-framework=$(PREFIX)/Library/Frameworks

build: expand apply
	cd $(SRC)/$(BUILD); \
        $(MAKE) DB=$(PREFIX)/db $(COMP_OPT) frameworkinstallframework; \
        $(MAKE) DB=$(PREFIX)/db $(COMP_OPT) frameworkinstallapps
	mkdir -p $(BUILD_ROOT)/$(SNAP)/$(SITE)

snap: 
	cd $(BUILD_ROOT); \
        tar -cvzf $(PYTHON)/python-$(SNAP)-$(RELVER).tar.gz \
                  $(SNAP)/Library/Frameworks/Python.framework \
            --exclude site-packages \
            --exclude test; \
	$(MD5) $(PYTHON)/python-$(SNAP)-$(RELVER).tar.gz > $(PYTHON)/python-$(SNAP)-$(RELVER).tar.gz.md5

Python-$(VERSION).tgz:
	$(CURL) http://builds.o11n.org/external/Python-$(VERSION).tgz
	$(CURL) http://builds.o11n.org/external/Python-$(VERSION).tgz.md5

sources: Python-$(VERSION).tgz

Python-$(VERSION)-expanded: Python-$(VERSION).tgz
	tar xvzf Python-$(VERSION).tgz
	touch Python-$(VERSION)-expanded

expand: Python-$(VERSION)-expanded

else

$(SRC)/$(BUILD)/Makefile:
	cd $(SRC); mkdir -p $(BUILD); cd $(BUILD); \
	../configure --prefix=$(PREFIX) $(CONF_DBG)

bzip2-$(BZIP2VERSION)/libbz2.a:
	make -C bzip2-$(BZIP2VERSION) libbz2.a

build: expand bzip2-$(BZIP2VERSION)/libbz2.a apply
	install -D bzip2-$(BZIP2VERSION)/libbz2.a $(PREFIX)/lib/libbz2.a
	install -D bzip2-$(BZIP2VERSION)/bzlib.h $(PREFIX)/include/bzlib.h
	$(MAKE) -C $(SRC)/$(BUILD) DB=$(PREFIX)/db $(COMP_OPT) install
	mkdir -p $(BUILD_ROOT)/$(SNAP)/$(SITE)

snap: 
	cd $(BUILD_ROOT); \
        tar -cvzf $(PYTHON)/python-$(SNAP)-$(RELVER).tar.gz \
                  $(SNAP)/bin/idle $(SNAP)/bin/python* \
                  $(SNAP)/lib/python* \
                  $(SNAP)/include/python* \
            --exclude site-packages \
            --exclude test; \
	$(MD5) $(PYTHON)/python-$(SNAP)-$(RELVER).tar.gz > $(PYTHON)/python-$(SNAP)-$(RELVER).tar.gz.md5

Python-$(VERSION).tgz:
	$(CURL) http://builds.o11n.org/external/Python-$(VERSION).tgz
	$(CURL) http://builds.o11n.org/external/Python-$(VERSION).tgz.md5

bzip2-$(BZIP2VERSION).tar.gz:
	$(CURL) http://builds.o11n.org/external/bzip2-$(BZIP2VERSION).tar.gz
	$(CURL) http://builds.o11n.org/external/bzip2-$(BZIP2VERSION).tar.gz.md5

sources: Python-$(VERSION).tgz bzip2-$(BZIP2VERSION).tar.gz

Python-$(VERSION)-expanded: Python-$(VERSION).tgz
	tar xvzf Python-$(VERSION).tgz
	touch Python-$(VERSION)-expanded

bzip2-$(BZIP2VERSION)-expanded: bzip2-$(BZIP2VERSION).tar.gz
	tar xvzf bzip2-$(BZIP2VERSION).tar.gz
	touch bzip2-$(BZIP2VERSION)-expanded

expand: Python-$(VERSION)-expanded bzip2-$(BZIP2VERSION)-expanded

endif

apply: $(SRC)/$(BUILD)/Makefile patches
	patch -Nup0 < patches; echo ok

clean:
	rm -rf $(SRC)/$(BUILD)

endif

upload: python-$(SNAP)-$(RELVER).tar.gz
	scp python-$(SNAP)-$(RELVER).tar.gz $(UPLOAD)
	scp python-$(SNAP)-$(RELVER).tar.gz.md5 $(UPLOAD)

install: python-$(SNAP)-$(RELVER).tar.gz
	tar -C $(CHANDLERBIN) -xvzf python-$(SNAP)-$(RELVER).tar.gz

_realclean::
	rm -fr zlib-* bzip2-*
