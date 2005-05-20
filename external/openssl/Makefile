
include ../Makefile.inc

VERSION=0.9.7g
RELVER=$(VERSION)-1
OPENSSL=$(BUILD_ROOT)/openssl
SRC=$(OPENSSL)/openssl-$(VERSION)

BUILD=build_$(SNAP)

ifeq ($(OS),Cygwin)
# Build using Visual C++ compiler
ifeq ($(DEBUG),1)
MK1MF=sed -e "s/mk1mf\.pl/mk1mf\.pl debug/" ms/do_masm.bat > ms/do_masm_debug.bat
OUT32DLL=out32dll.dbg
DOMASM=do_masm_debug.bat
else
MK1MF=echo "Defaults work"
OUT32DLL=out32dll
DOMASM=do_masm.bat
endif

$(SRC)/$(BUILD)/ms/$(DOMASM):
	cd $(SRC); mkdir $(BUILD); cp Makefile.org *.h $(BUILD)/; \
	cp -r crypto ssl apps certs tools util ms include test fips $(BUILD)/; \
	cd $(BUILD);\
	$(MK1MF);\
	chmod a+x ms/$(DOMASM);

openssl: apply $(SRC)/$(BUILD)/ms/$(DOMASM)
	cd $(SRC)/$(BUILD); \
	MAKEFLAGS=; \
	perl ../Configure --openssldir=$(PREFIX) --install_prefix=$(PREFIX) $(CONF_OPT) VC-WIN32; \
	ms/$(DOMASM); \
	nmake -f ms/ntdll.mak;\
	cd $(OUT32DLL); \
	../ms/test.bat; \
	cp -f ssleay32.dll $(PREFIX)/bin/; \
	cp -f libeay32.dll $(PREFIX)/bin/; \
	cp -f ssleay32.lib $(PREFIX)/lib/; \
	cp -f libeay32.lib $(PREFIX)/lib/; \
	cp -fr  ../inc32/openssl $(PREFIX)/Include

# snap target can be empty on Windows because we will install the OpenSSL
# DLLs during M2Crypto build, as we'll be copying the DLLs into site-packages
# to make sure Chandler will find our DLLs and not anything in Windows
# system directories.
snap: 

# M2Crypto upload handles this as well
upload:

# and this
install:

else

$(SRC)/$(BUILD):
	cd $(SRC); mkdir $(BUILD);\
	cp -r Configure Makefile.org *.h crypto ssl apps certs tools util doc include fips $(BUILD)/

openssl: apply $(SRC)/$(BUILD)
	cd $(SRC)/$(BUILD);\
	../config shared --openssldir=$(PREFIX) $(CONF_OPT);\
	$(MAKE);\
	$(MAKE) install

upload: openssl-$(SNAP)-$(RELVER).tar.gz
	scp openssl-$(SNAP)-$(RELVER).tar.gz $(UPLOAD)
	scp openssl-$(SNAP)-$(RELVER).tar.gz.md5 $(UPLOAD)

install: openssl-$(SNAP)-$(RELVER).tar.gz
	tar -C $(CHANDLERBIN) -xvzf openssl-$(SNAP)-$(RELVER).tar.gz

ifeq ($(OS),Darwin)

snap: 
	cd $(BUILD_ROOT); \
	tar -cvzf $(OPENSSL)/openssl-$(SNAP)-$(RELVER).tar.gz \
		   $(SNAP)/lib/libcrypto.0.9.7.dylib \
		   $(SNAP)/lib/libcrypto.0.dylib \
		   $(SNAP)/lib/libcrypto.dylib \
		   $(SNAP)/lib/libssl.0.9.7.dylib \
		   $(SNAP)/lib/libssl.0.dylib \
		   $(SNAP)/lib/libssl.dylib; \
	$(MD5) $(OPENSSL)/openssl-$(SNAP)-$(RELVER).tar.gz > $(OPENSSL)/openssl-$(SNAP)-$(RELVER).tar.gz.md5

else

snap: 
	cd $(BUILD_ROOT); \
	tar -cvzf $(OPENSSL)/openssl-$(SNAP)-$(RELVER).tar.gz \
		   $(SNAP)/lib/libcrypto.so.0.9.7 \
		   $(SNAP)/lib/libcrypto.so.0 \
		   $(SNAP)/lib/libcrypto.so \
		   $(SNAP)/lib/libssl.so.0.9.7 \
		   $(SNAP)/lib/libssl.so.0 \
		   $(SNAP)/lib/libssl.so; \
	$(MD5) $(OPENSSL)/openssl-$(SNAP)-$(RELVER).tar.gz > $(OPENSSL)/openssl-$(SNAP)-$(RELVER).tar.gz.md5

endif # if OS X or linux
endif # if Cygwin or not

openssl-$(VERSION).tar.gz:
	$(CURL) http://builds.o11n.org/external/openssl-$(VERSION).tar.gz
	$(CURL) http://builds.o11n.org/external/openssl-$(VERSION).tar.gz.md5

sources: openssl-$(VERSION).tar.gz

openssl-$(VERSION)-expanded: openssl-$(VERSION).tar.gz
	tar xvzf openssl-$(VERSION).tar.gz
	touch openssl-$(VERSION)-expanded

expand: openssl-$(VERSION)-expanded

apply:
	patch -Nup0 < patches-$(VERSION); echo ok

clean:
	rm -rf $(SRC)/$(BUILD)

build: expand openssl
