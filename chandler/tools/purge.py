import os, sys

def purgeDirs(path=os.curdir, verbose=True, dry_run=False):
    """Purge orphaned .pyc/.pyo files and remove emptied directories"""

    for dirname,dirs,files in os.walk(path, topdown=False):        
        to_purge = [
            f for f in files
            if (f.endswith('.pyc') or f.endswith('.pyo'))
            and f[:-1] not in files     # don't purge if it has a .py
        ]
        for f in to_purge:
            filename = os.path.join(dirname,f)
            if verbose:
                print "deleting", filename
            if not dry_run:
                os.unlink(filename)

        if to_purge and files==to_purge:
            for d in dirs:
                # Do any of the subdirectories still exist?
                if os.path.exists(os.path.join(dirname,d)):
                    # If so, we've done all we can
                    break
            else:
                # Go ahread and remove the current directory
                if verbose:
                    print "removing ", dirname
                if not dry_run:
                    os.removedirs(dirname)

if __name__ == '__main__':
    from optparse import OptionParser

    parser = OptionParser(usage="usage: %prog [options] directory")
    parser.add_option(
        "-n", "--dry-run", dest="dry_run", action="store_true", default=False,
        help="don't actually delete anything"
    )
    parser.add_option("-q", "--quiet",
        action="store_false", dest="verbose", default=True,
        help="don't display the files/dirs being removed"
    )

    (options, args) = parser.parse_args()

    if options.dry_run and not options.verbose:
        print "Using both -n and -q makes no sense.  Use --help for options."
        sys.exit(2)

    if not args:
        print "No directories specified.  Use --help for options."
        sys.exit(2)

    for path in args:
        purgeDirs(path, options.verbose, options.dry_run)

