
include ../Makefile.inc

VERSION=0.9.7d
RELVER=$(VERSION)-1
OPENSSL=$(BUILD_ROOT)/openssl
SRC=$(OPENSSL)/openssl-$(VERSION)

BUILD=build_$(SNAP)

.PHONY: openssl

#XXX Why do we need this for?
ifeq ($(OS),Cygwin)
BINFILE=openssl.exe
else
BINFILE=openssl
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

openssl:
	cd $(SRC); \
	MAKEFLAGS=;\
	perl Configure $(CONF_OPT) VC-WIN32; \
	ms/do_masm.bat; \
	nmake -f ms/ntdll.mak;\
	cd out32dll; \
	../ms/test.bat; \
	echo 'Installing...';\
	cp -f ssleay32.dll $(PREFIX)/bin/; \
	cp -f libeay32.dll $(PREFIX)/bin/; \
	cp -f ssleay32.lib $(PREFIX)/bin/libs/; \
	cp -f libeay32.lib $(PREFIX)/bin/libs/; \
	cp -fr ../inc32/openssl $(PREFIX)/bin/Include/openssl;\
	echo 'Installation done.'

snap: 
	cd $(BUILD_ROOT); \
        tar -cvzf $(SRC)/openssl-$(SNAP)-$(RELVER).tar.gz \
                   $(SNAP)/openssl.cnf \
                   $(SNAP)/bin/c_rehash \
                   $(SNAP)/bin/$(BINFILE) \
                   $(SNAP)/include/ \
                   $(SNAP)/lib/libcrypto.a \
                   $(SNAP)/lib/libssl.a  \
                   $(SNAP)/lib/pkgconfig/openssl.pc \
                   $(SNAP)/misc \
                   $(SNAP)/private \
                   $(SNAP)/certs

else

openssl:   $(SRC)/Makefile
	cd $(SRC); \
        $(MAKE) ; $(MAKE) install 

$(SRC)/Makefile:
	cd $(SRC); \
	./config --prefix=$(PREFIX) --openssldir=$(PREFIX) $(CONF_OPT)

snap: 
	cd $(BUILD_ROOT); \
        tar -cvzf $(SRC)/openssl-$(SNAP)-$(RELVER).tar.gz \
                   $(SNAP)/openssl.cnf \
                   $(SNAP)/bin/c_rehash \
                   $(SNAP)/bin/$(BINFILE) \
                   $(SNAP)/include/ \
                   $(SNAP)/lib/libcrypto.a \
                   $(SNAP)/lib/libssl.a  \
                   $(SNAP)/lib/pkgconfig/openssl.pc \
                   $(SNAP)/misc \
                   $(SNAP)/private \
                   $(SNAP)/certs

endif

upload: openssl-$(SNAP)-$(RELVER).tar.gz
	scp openssl-$(SNAP)-$(RELVER).tar.gz $(UPLOAD)

expand: openssl-$(VERSION).tar.gz
	tar xvzf openssl-$(VERSION).tar.gz
	rm -f openssl-$(VERSION)/Makefile

apply: expand patches
	patch -Nup0 < patches; echo ok

clean:
	rm -rf $(SRC)

build: openssl
