
VERSION=1.3-final
PYLUCENE=$(BUILD_ROOT)/persistence/PyLucene
LUCENE=$(PYLUCENE)/lucene-$(VERSION)
OS=$(shell uname)

ifeq ($(DEBUG),1)

COMP_OPT=DEBUG=1
SNAP=debug

else

COMP_OPT=
SNAP=release

endif

ifeq ($(OS),Darwin)

SITE=Library/Frameworks/Python.framework/Versions/2.3/lib/python2.3/site-packages
OS_MAKE=Makefile.osx

else

SITE=lib/python2.3/site-packages
OS_MAKE=Makefile.linux

endif

BUILD=build_$(SNAP)


ifeq ($(OS),Darwin)

snap: 
	cd $(BUILD_ROOT); \
        tar -cvzf $(PYLUCENE)/$(SNAP).tar.gz \
                  $(SNAP)/$(SITE)/PyLucene.py \
                  $(SNAP)/$(SITE)/_PyLucene.so \
                  $(SNAP)/db/lib/libdb_java-4.2.jnilib \
                  $(SNAP)/db/lib/libdb_java-4.2.la \
                  $(SNAP)/lib/libgcc_s.1.0.dylib \
                  $(SNAP)/lib/libgcj.4.dylib \
                  $(SNAP)/lib/libstdc++.6.dylib

else

snap: 
	cd $(BUILD_ROOT); \
        tar -cvzf $(PYLUCENE)/$(SNAP).tar.gz \
                  $(SNAP)/$(SITE)/PyLucene.py \
                  $(SNAP)/$(SITE)/_PyLucene.so \
                  $(SNAP)/db/lib/libdb_java-4.2.so \
                  $(SNAP)/lib/libgcc_s.so.1 \
                  $(SNAP)/lib/libgcj.so.4 \
                  $(SNAP)/lib/libstdc++.so.5

endif

default: all

apply: patches
	patch -Nup0 < patches; echo ok

build: apply
	$(MAKE) -f $(OS_MAKE) GCJ=$(GCJ_HOME) $(COMP_OPT) \
                              DBVERSION=4.2.52 VERSION=$(VERSION) \
                              all install

expand: lucene-$(VERSION)-src.tar.gz
	tar xvzf lucene-$(VERSION)-src.tar.gz

clean:
	rm -rf $(BUILD)

all: build
