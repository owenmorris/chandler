
include ../Makefile.inc

VERSION=1.3-final
RELVER=0.3-1
PYLUCENE=$(INTERNAL)/PyLucene
LUCENE=$(PYLUCENE)/lucene-$(VERSION)
DB=$(EXTERNAL)/persistence/db/db-4.2.52

ifeq ($(DEBUG),1)
COMP_OPT=DEBUG=1
SUFFIX=d
_SUFFIX=_d
else
COMP_OPT=
SUFFIX=
_SUFFIX=
endif

ifeq ($(OS),Cygwin)
OS_MAKE=Makefile.mingw
MAKE=nmake
else
ifeq ($(OS),Darwin)
OS_MAKE=Makefile.osx
else
OS_MAKE=Makefile.linux
endif
endif

BUILD=build_$(SNAP)

ifeq ($(OS),Cygwin)

build: sources apply
	MAKEFLAGS=; \
	. $(BUILD_ROOT)/cygenv.sh; \
	echo PATH is $(PATH); \
	$(MAKE) -f $(OS_MAKE) GCJ=`cygpath -aw $(GCJ_HOME)` $(COMP_OPT) \
                              DB=`cygpath -aw $(DB)` \
                              RELDIR=`cygpath -aw $(BUILD_ROOT)/$(SNAP)` \
                              VERSION=$(VERSION) \
                              all install

snap: 
	cd $(BUILD_ROOT); \
        tar -cvzf $(PYLUCENE)/PyLucene-$(SNAP)-$(RELVER).tar.gz \
                  $(SNAP)/$(SITE)/PyLucene.py \
                  $(SNAP)/$(SITE)/_PyLucene$(_SUFFIX).pyd \
                  $(SNAP)/bin/libdb_java42$(SUFFIX).dll

else

ifeq ($(OS),Darwin)

snap: 
	cd $(BUILD_ROOT); \
        tar -cvzf $(PYLUCENE)/PyLucene-$(SNAP)-$(RELVER).tar.gz \
                  $(SNAP)/$(SITE)/PyLucene.py \
                  $(SNAP)/$(SITE)/_PyLucene.so \
                  $(SNAP)/db/lib/libdb_java-4.2.jnilib \
                  $(SNAP)/db/lib/libdb_java-4.2.la \
                  $(SNAP)/lib/libgcc_s.1.0.dylib \
                  $(SNAP)/lib/libgcj.5.dylib \
                  $(SNAP)/lib/libstdc++.6.dylib

else

snap: 
	cd $(BUILD_ROOT); \
        tar -cvzf $(PYLUCENE)/PyLucene-$(SNAP)-$(RELVER).tar.gz \
                  $(SNAP)/$(SITE)/PyLucene.py \
                  $(SNAP)/$(SITE)/_PyLucene.so \
                  $(SNAP)/db/lib/libdb_java-4.2.so \
                  $(SNAP)/lib/libgcc_s.so.1 \
                  $(SNAP)/lib/libgcj.so.4 \
                  $(SNAP)/lib/libstdc++.so.5

endif

build: sources apply
	MAKEFLAGS=; \
	$(MAKE) -f $(OS_MAKE) GCJ=$(GCJ_HOME) $(COMP_OPT) \
                              DB=$(DB) VERSION=$(VERSION) \
                              RELDIR=$(BUILD_ROOT)/$(SNAP) \
                              all install

endif

sources:
	if [ ! -d lucene-$(VERSION) ]; then \
            tar xvzf lucene-$(VERSION)-src.tar.gz; \
        fi

apply: patches
	patch -Nup0 < patches; echo ok
	make -C $(BUILD_ROOT)/persistence/db apply

clean:
	rm -rf $(BUILD)

upload: PyLucene-$(SNAP)-$(RELVER).tar.gz
	scp PyLucene-$(SNAP)-$(RELVER).tar.gz $(UPLOAD)
