
VERSION=2.4.3
RELVER=$(VERSION)-$(BRANCH_REV_PREFIX)3

BZIP2VERSION=1.0.3
ZLIBVERSION=1.2.3

include $(BUILD_ROOT)/Makefile.inc

PYTHON=$(BUILD_ROOT)/python
SRC=$(PYTHON)/Python-$(VERSION)
TARBALL=python-$(SNAP)-$(RELVER).tar.gz

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

sources:: Python-$(VERSION).tar.bz2

expand:: Python-$(VERSION)-expanded


ifeq ($(OS),Cygwin)

BINDIR=$(PREFIX)/bin
PV=$(subst .,,$(PYTHON_VER))

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

compile: bzip2 zlib
	(cd win32/$(VERSION); \
      tar -cf - *.sln *.vcproj) | tar -C $(SRC)/PCbuild -xf -
	cd $(SRC)/PCbuild; SNAP=$(SNAP) devenv.com pcbuild.sln /build $(Snap)

installext:
	mkdir -p $(BINDIR)/DLLs $(BINDIR)/Include $(BINDIR)/Lib $(BINDIR)/libs
	tar -C $(SRC)/PCbuild \
      -cf - python$(SUFFIX).exe \
            pythonw$(SUFFIX).exe \
            python$(PV)$(SUFFIX).dll | tar -C $(BINDIR) -xvf -
	tar -C $(SRC)/PCbuild \
      -cf - python$(PV)$(SUFFIX).lib \
            python$(PV)$(SUFFIX).exp | tar -C $(BINDIR)/libs -xvf -
	(cd $(SRC)/Lib; tar -cf - *.py) | tar -C $(BINDIR)/Lib -xvf -
	(cd $(SRC)/PCbuild; tar -cf - *.pyd) | tar -C $(BINDIR)/DLLs -xvf -
	for mod in compiler distutils email encodings hotshot xml logging; \
  do \
      (cd $(SRC)/Lib; \
      tar -cf - `find $$mod -name '*.py'`) | tar -C $(BINDIR)/Lib -xvf - ; \
  done
	(cd $(SRC)/Include; tar -cf - *.h) | tar -C $(BINDIR)/Include -xvf -
	cp -p $(SRC)/PC/pyconfig.h $(BINDIR)/Include

sources:: bzip2-$(BZIP2VERSION).tar.gz zlib-$(ZLIBVERSION).tar.gz

expand:: bzip2-$(BZIP2VERSION)-expanded zlib-$(ZLIBVERSION)-expanded
ifeq ($(VERSION),2.4)
	rm -f $(SRC)/PCbuild/pcbuild.sln
endif

clean:
	rm -rf bzip2-$(BZIP2VERSION)/$(BUILD) bzip2-$(BZIP2VERSION)/libbz2$(SUFFIX).lib
	rm -rf zlib-$(ZLIBVERSION)/$(BUILD) zlib-$(ZLIBVERSION)/zlib$(SUFFIX).lib
	cd $(SRC)/PCbuild; devenv.com pcbuild.sln /clean $(Snap); echo ok
	rm -f $(SRC)/PCbuild/pcbuild.sln
	rm -f $(CHANDLERBIN)/$(SNAP)/$(TARBALL).inst

binaries: strip
	find $(BUILD_ROOT)/$(SNAP)/$(SITE)/libs -name "*.pyc" | xargs rm -f
	find $(BUILD_ROOT)/$(SNAP)/$(SITE)/libs -name "*.pyo" | xargs rm -f
	cd $(BUILD_ROOT); \
        tar -cvzf $(PYTHON)/python-$(SNAP)-$(RELVER).tar.gz \
            --exclude site-packages \
            --exclude test \
                  $(SNAP)/bin/python*.* $(SNAP)/bin/libs \
                  $(SNAP)/bin/DLLs $(SNAP)/bin/Include $(SNAP)/bin/Lib

else

ifeq ($(OS),Darwin)

$(SRC)/$(BUILD)/Makefile: patches-$(VERSION)-$(OS)
	patch -Nup0 < patches-$(VERSION)-$(OS); echo ok
	mkdir -p $(SRC)/$(BUILD)
	cd $(SRC)/$(BUILD); \
      MACOSX_DEPLOYMENT_TARGET=$(MACOSX_DEPLOYMENT_TARGET) \
          LDFLAGS="-L$(PREFIX)/lib $(LDFLAGS)" \
          CPPFLAGS="-I$(PREFIX)/include $(CPPFLAGS)" \
          DYNLOADFILE=dynload_shlib.o \
          ../configure --prefix=$(PREFIX) $(CONF_DBG) \
                       --enable-framework=$(PREFIX)/Library/Frameworks \
                       --disable-ipv6

build: expand apply $(SRC)/$(BUILD)/Makefile
	MACOSX_DEPLOYMENT_TARGET=$(MACOSX_DEPLOYMENT_TARGET) \
        SNAP=$(SNAP) \
        ARCH=$(ARCH) \
        PREFIX=$(PREFIX) \
        $(MAKE) -C $(SRC)/$(BUILD) $(COMP_OPT) \
                frameworkinstallframework frameworkinstallapps
	mkdir -p $(BUILD_ROOT)/$(SNAP)/$(SITE)

binaries: strip
	find $(BUILD_ROOT)/$(SNAP)/Library/Frameworks/Python.framework -name "*.pyc" | xargs rm -f
	find $(BUILD_ROOT)/$(SNAP)/Library/Frameworks/Python.framework -name "*.pyo" | xargs rm -f
	tar -C $(BUILD_ROOT) \
            -cvzf $(PYTHON)/python-$(SNAP)-$(RELVER).tar.gz \
            --exclude site-packages \
            --exclude test \
            $(SNAP)/Library/Frameworks/Python.framework

else

$(SRC)/$(BUILD)/Makefile:
	cd $(SRC); \
      mkdir -p $(BUILD); \
      cd $(BUILD); \
      ../configure --prefix=$(PREFIX) $(CONF_DBG)

bzip2-$(BZIP2VERSION)/libbz2.a:
	make -C bzip2-$(BZIP2VERSION) libbz2.a

build: expand bzip2-$(BZIP2VERSION)/libbz2.a apply $(SRC)/$(BUILD)/Makefile
	install -D bzip2-$(BZIP2VERSION)/libbz2.a $(PREFIX)/lib/libbz2.a
	install -D bzip2-$(BZIP2VERSION)/bzlib.h $(PREFIX)/include/bzlib.h
	SNAP=$(SNAP) $(MAKE) -C $(SRC)/$(BUILD) $(COMP_OPT) install
	mkdir -p $(BUILD_ROOT)/$(SNAP)/$(SITE)

binaries: strip
	cd $(BUILD_ROOT); \
	find $(SNAP)/lib/python*/ -name "*.pyc" | xargs rm -f; \
	find $(SNAP)/lib/python*/ -name "*.pyo" | xargs rm -f; \
        tar -cvzf $(PYTHON)/python-$(SNAP)-$(RELVER).tar.gz \
            --exclude site-packages \
            --exclude test \
                  $(SNAP)/bin/idle $(SNAP)/bin/python* \
                  $(SNAP)/lib/python* \
                  $(SNAP)/include/python*

sources:: bzip2-$(BZIP2VERSION).tar.gz

expand:: bzip2-$(BZIP2VERSION)-expanded

endif

ifneq (/,$(SRC)/$(BUILD))
clean:
	rm -rf $(SRC)/$(BUILD)
endif

endif

patches-$(VERSION):
	diff -u Python-$(VERSION)/Mac/OSX/Makefile Python-$(VERSION)-patched/Mac/OSX/Makefile > patches-$(VERSION); true
	diff -u Python-$(VERSION)/PC/getpathp.c Python-$(VERSION)-patched/PC/getpathp.c >> patches-$(VERSION); true
	diff -u Python-$(VERSION)/setup.py Python-$(VERSION)-patched/setup.py >> patches-$(VERSION); true
	diff -u Python-$(VERSION)/configure Python-$(VERSION)-patched/configure >> patches-$(VERSION); true
	diff -u Python-$(VERSION)/Makefile.pre.in Python-$(VERSION)-patched/Makefile.pre.in >> patches-$(VERSION); true

apply: patches-$(VERSION)
	patch -Nup0 < patches-$(VERSION); echo ok
	rm -rf Python-$(VERSION)/Lib/bsddb

Python-$(VERSION).tar.bz2:
	$(CURL) http://builds.osafoundation.org/external/Python-$(VERSION).tar.bz2

bzip2-$(BZIP2VERSION).tar.gz:
	$(CURL) http://builds.osafoundation.org/external/bzip2-$(BZIP2VERSION).tar.gz

zlib-$(ZLIBVERSION).tar.gz:
	$(CURL) http://builds.osafoundation.org/external/zlib-$(ZLIBVERSION).tar.gz

Python-$(VERSION)-expanded: Python-$(VERSION).tar.bz2
	bunzip2 -c Python-$(VERSION).tar.bz2 | tar -xvf -
	touch Python-$(VERSION)-expanded

bzip2-$(BZIP2VERSION)-expanded: bzip2-$(BZIP2VERSION).tar.gz
	tar xvzf bzip2-$(BZIP2VERSION).tar.gz
	touch bzip2-$(BZIP2VERSION)-expanded

zlib-$(ZLIBVERSION)-expanded: zlib-$(ZLIBVERSION).tar.gz
	tar xvzf zlib-$(ZLIBVERSION).tar.gz
	touch zlib-$(ZLIBVERSION)-expanded

install: $(TARBALL)
	cp -p $(TARBALL) $(CHANDLERARCHIVES)

_realclean::
	@rm -rf zlib-* bzip2-*
