#-*- Mode: Makefile; -*-
#
# internal
#

EXTERNAL=$(BUILD_ROOT)
INTERNAL=$(dir $(BUILD_ROOT))internal

include $(EXTERNAL)/Makefile.inc

env::
	@echo INTERNAL is $(INTERNAL)
