
include ../Makefile.inc

VERSION=0.9.7d
RELVER=$(VERSION)-1
OPENSSL=$(BUILD_ROOT)/openssl
SRC=$(OPENSSL)/openssl-$(VERSION)

BUILD=build_$(SNAP)

.PHONY: openssl

ifeq ($(OS),Darwin)
PLATFORM='darwin-ppc-cc'
endif
ifeq ($(OS),Linux)
# XXX fix later, just for now
PLATFORM='linux-pentium'
endif

REAL_OS=unknown

ifeq ($(OS),Cygwin)
  REAL_OS=WINNT
endif

ifeq ($(OS),WINNT)
  REAL_OS=WINNT
endif

ifeq ($(REAL_OS),WINNT)
# Build using Visual C++ compiler
# TODO: debug version, and the ability to build both debug & release simult.
#       Do we need patches file or can we get rid of it?

$(SRC)/$(BUILD)/Makefile:  $(SRC)/Configure
	cd $(SRC); mkdir $(BUILD); cp Makefile.org *.h $(BUILD)/; \
	cp -r crypto ssl apps certs tools util include $(BUILD)/;cd $(BUILD);\
	MAKEFLAGS=;\
	perl ../Configure --openssldir=$(PREFIX) --install_prefix=$(PREFIX) $(CONF_OPT) VC-WIN32; \


openssl: $(SRC)/$(BUILD)/Makefile.ssl
	ms/do_masm.bat; \
	nmake -f ms/ntdll.mak;\
	cd out32dll; \
	../ms/test.bat; \
	echo 'Installing...';\
	cp -f ssleay32.dll $(PREFIX)/bin/; \
	cp -f libeay32.dll $(PREFIX)/bin/; \
	cp -f ssleay32.lib $(PREFIX)/lib/; \
	cp -f libeay32.lib $(PREFIX)/lib/; \
	cp -fr ../inc32/openssl $(PREFIX)/Include/;\
	echo 'Installation done.'

snap: 
	cd $(BUILD_ROOT); \
	tar -cvzf $(OPENSSL)/$(SNAP).tar.gz \
                   $(SNAP)/bin/ssleay32.dll \
                   $(SNAP)/bin/libeay32.dll \
                   $(SNAP)/include/openssl \
                   $(SNAP)/lib/ssleay32.lib \
                   $(SNAP)/lib/libeay32.lib  \
                   $(SNAP)/misc \
                   $(SNAP)/private \
                   $(SNAP)/certs

else

openssl:   $(SRC)/$(BUILD)/Makefile
	cd $(SRC)/$(BUILD); \
	$(MAKE) -f Makefile.ssl; $(MAKE) -f Makefile.ssl install 

$(SRC)/$(BUILD)/Makefile: $(SRC)/Configure
	cd $(SRC); mkdir $(BUILD); cp Makefile.org *.h $(BUILD)/; \
	cp -r crypto ssl apps certs tools util include $(BUILD)/;cd $(BUILD);\
	perl ../Configure --openssldir=$(PREFIX) $(CONF_OPT) $(PLATFORM)

snap: 
	cd $(BUILD_ROOT); \
	tar -cvzf $(OPENSSL)/$(SNAP).tar.gz \
                   $(SNAP)/openssl.cnf \
                   $(SNAP)/bin/c_rehash \
                   $(SNAP)/bin/openssl \
                   $(SNAP)/include/ \
                   $(SNAP)/lib/libcrypto.a \
                   $(SNAP)/lib/libssl.a  \
                   $(SNAP)/lib/pkgconfig/openssl.pc \
                   $(SNAP)/misc \
                   $(SNAP)/private \
                   $(SNAP)/certs

endif

$(SRC): apply

expand: openssl-$(VERSION).tar.gz
	tar xvzf openssl-$(VERSION).tar.gz
	rm -f openssl-$(VERSION)/Makefile

apply: expand patches
	patch -Nup0 < patches; echo ok

clean:
	rm -rf $(SRC)/$(BUILD)

build: openssl
