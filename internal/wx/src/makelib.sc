##############################################################################
# Name:			src/makelib.sc
# Purpose:		build library Digital Mars 8.33 compiler
# Author:		Chris Elliott
# Created:		21.01.03
# RCS-ID:		$Id: makelib.sc 5166 2005-04-29 01:36:53Z davids $
# Licence:		wxWindows licence
##############################################################################




all:  $(LIBTARGET) 

$(LIBTARGET): $(OBJECTS)
    lib -c $(LIBTARGET) $(OBJECTS)


clean: 
	-del $(THISDIR)\*.obj
	-del $(LIBTARGET)

