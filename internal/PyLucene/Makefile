
VERSION=1.3-final
PYLUCENE=$(BUILD_ROOT)/persistence/PyLucene
LUCENE=$(PYLUCENE)/lucene-$(VERSION)

ifeq ($(DEBUG),1)

COMP_OPT=DEBUG=1
SNAP=debug

else

COMP_OPT=
SNAP=release

endif

BUILD=build_$(SNAP)
PYTHON_SITE=$(SNAP)/Library/Frameworks/Python.framework/Versions/2.3/lib/python2.3/site-packages


default: all

apply: patches
	patch -Nup0 < patches; echo ok

build: apply
	$(MAKE) -f Makefile.osx GCJ=$(GCJ_HOME) $(COMP_OPT) \
                                DBVERSION=4.2.52 VERSION=$(VERSION) \
                                all install

expand: lucene-$(VERSION).tar.gz
	tar xvzf lucene-$(VERSION).tar.gz

snap: 
	cd $(BUILD_ROOT); \
        tar -cvzf $(PYLUCENE)/$(SNAP).tar.gz \
                  $(PYTHON_SITE)/PyLucene.py \
                  $(PYTHON_SITE)/_PyLucene.so \
                  $(SNAP)/db/lib/libdb_java-4.2.jnilib \
                  $(SNAP)/db/lib/libdb_java-4.2.la \
                  $(SNAP)/lib/libgcc_s.1.0.dylib \
                  $(SNAP)/lib/libgcj.4.dylib \
                  $(SNAP)/lib/libstdc++.6.dylib

clean:
	rm -rf $(BUILD)

all: build
