Launcher for Linux

There are two programs:  chandler and chandler_bin.  The former goes through
some steps to determine which directory it actually resides in (regardless of
how it was invoked -- via an absolute or relative path, or found via the PATH
environment variable), and then prepends the LD_LIBRARY_PATH env var with the
lib/ directory below the chandler executable.  It then executes the
chandler_bin program (which has the Python interpreter embedded in it) from
the lib/ directory, and chandler_bin starts processing Chandler.py.

The expected directory layout is:

/path/to/app/
   application/
      Application.py
      etc.
   lib/
      chandler_bin*
      libwx_gtk_XYZZY_.so
      python2.3/
   parcels/
      calendar/
      contacts/
      etc.
   chandler*
   Chandler.py
