
VERSION=2.4
RIJNDAEL=$(BUILD_ROOT)/rijndael
SRC=$(RIJNDAEL)/rijndael-$(VERSION)

include $(BUILD_ROOT)/Makefile.inc

BUILD=rijndael-$(VERSION)/$(SNAP)

MANIFEST=$(SNAP)/$(SITE)/$(RIJNDAEL_LIB) \
         $(SNAP)/$(SITE)/rijndael.py

rijndael_wrap.cxx: rijndael.i
	$(SWIG) -modern -I$(SRC) -c++ -python rijndael.i


ifeq ($(OS),Cygwin)

ifeq ($(DEBUG),1)
_SUFFIX=_d
SUFFIX=d
CCFLAGS=-Od -Z7 -DWIN32
else
_SUFFIX=
SUFFIX=
CCFLAGS=-Ox -DWIN32
endif

CXX=cl.exe
RIJNDAEL_LIB=_rijndael$(_SUFFIX).pyd

$(BUILD)/rijndael.obj:
	$(CXX) -nologo $(CCFLAGS) -c -Fo`cygpath -aw $(BUILD)`\\ -I`cygpath -aw $(SRC)` `cygpath -aw $(SRC)/rijndael.cpp`

$(BUILD)/$(RIJNDAEL_LIB): rijndael_wrap.cxx $(BUILD)/rijndael.obj
	$(CXX) -nologo $(CCFLAGS) -I`cygpath -aw $(PYTHON_INC)` -I`cygpath -aw $(SRC)` -Tprijndael_wrap.cxx -Fe`cygpath -aw $@` -LD$(SUFFIX) -link -libpath:`cygpath -aw $(PREFIX)/bin/libs` `cygpath -aw $(BUILD)/rijndael.obj` -nodefaultlib:libcmt$(SUFFIX)

else

CXX=g++
RIJNDAEL_LIB=_rijndael.so

$(BUILD)/rijndael.o: 
	$(CXX) $(CCFLAGS) -c -o $@ -I$(SRC) $(SRC)/rijndael.cpp

ifeq ($(OS),Darwin)

ifeq ($(DEBUG),1)
CCFLAGS=-g -Wno-long-double
else
CCFLAGS=-O3 -Wno-long-double
endif

$(BUILD)/$(RIJNDAEL_LIB): rijndael_wrap.cxx $(BUILD)/rijndael.o
	$(CXX) -bundle -o $@ $(CCFLAGS) -I$(PYTHON_INC) -I$(SRC) rijndael_wrap.cxx $(BUILD)/rijndael.o -undefined suppress -flat_namespace -multiply_defined suppress

else

ifeq ($(DEBUG),1)
CCFLAGS=-g -fPIC
else
CCFLAGS=-O3 -fPIC
endif

$(BUILD)/$(RIJNDAEL_LIB): rijndael_wrap.cxx $(BUILD)/rijndael.o
	$(CXX) -shared -o $@ $(CCFLAGS) -I$(PYTHON_INC) -I$(SRC) rijndael_wrap.cxx $(BUILD)/rijndael.o

endif
endif

$(BUILD):
	mkdir -p $(BUILD)

build: $(BUILD) $(BUILD)/$(RIJNDAEL_LIB)
	install rijndael.py $(PREFIX)/$(SITE)
	install $(BUILD)/$(RIJNDAEL_LIB) $(PREFIX)/$(SITE)

clean:
	rm -rf rijndael_wrap.cxx $(BUILD)

snap: 
	cd $(BUILD_ROOT); \
        tar -cvzf $(RIJNDAEL)/$(SNAP).tar.gz $(MANIFEST)
