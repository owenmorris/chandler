
VERSION=0.5.1
PYLUCENE=$(BUILD_ROOT)/PyLucene
SRC=$(PYLUCENE)/PyLucene-$(VERSION)

include $(BUILD_ROOT)/Makefile.inc


ifeq ($(OS),Cygwin)
ifeq ($(DEBUG),1)
SUFFIX=d
_SUFFIX=_d
else
SUFFIX=
_SUFFIX=
endif
PREFIX_PYTHON=$(PREFIX)/bin
PREFIX_DB=$(BUILD_ROOT)/persistence/db/db-4.2.52
MANIFEST=$(SNAP)/$(SITE)/PyLucene.py \
         $(SNAP)/$(SITE)/_PyLucene$(_SUFFIX).pyd \
         $(SNAP)/bin/libdb_java42$(SUFFIX).dll
else

ifeq ($(OS),Darwin)
PREFIX_PYTHON=$(PREFIX)/$(FRAMEWORK)
PREFIX_DB=$(PREFIX)/db
MANIFEST=$(SNAP)/$(SITE)/PyLucene.py \
         $(SNAP)/$(SITE)/_PyLucene.so \
         $(SNAP)/db/lib/libdb_java-4.2.jnilib \
         $(SNAP)/db/lib/libdb_java-4.2.la \
         $(SNAP)/lib/libgcc_s.1.0.dylib \
         $(SNAP)/lib/libgcj.5.dylib \
         $(SNAP)/lib/libstdc++.6.dylib
else

ifeq ($(OS),Linux)
PREFIX_PYTHON=$(PREFIX)
PREFIX_DB=$(PREFIX)/db
MANIFEST=$(SNAP)/$(SITE)/PyLucene.py \
         $(SNAP)/$(SITE)/_PyLucene.so \
         $(SNAP)/db/lib/libdb_java-4.2.so \
         $(SNAP)/lib/libgcc_s.so.1 \
         $(SNAP)/lib/libgcj.so.5 \
         $(SNAP)/lib/libstdc++.so.6
endif
endif
endif


apply: 
	if [ -f patches-$(VERSION) ]; then \
	   patch -Nup0 < patches-$(VERSION); echo ok; \
	fi

build: apply
	$(MAKE) -C $(SRC) \
            PREFIX=$(PREFIX) \
            PREFIX_PYTHON=$(PREFIX_PYTHON) \
            SWIG=$(SWIG) \
            GCJ_HOME=$(GCJ_HOME) \
            DB=$(BUILD_ROOT)/persistence/db/db-4.2.52 \
            PREFIX_DB=$(PREFIX_DB) \
            BUILD_DB=build_$(SNAP) \
            all install

clean:
	$(MAKE) -C $(SRC) clean

snap: 
	cd $(BUILD_ROOT); \
        tar -cvzf $(PYLUCENE)/$(SNAP).tar.gz $(MANIFEST)

expand: PyLucene-$(VERSION).tar.gz
	tar xvzf PyLucene-$(VERSION).tar.gz
