This plugin provides support for Flickr photo searches by user or tag in Chandler.

If you want to work on its code, you can use::

    RunPython setup.py develop

to install it in development mode (where you can make changes and have them
take effect whenever Chandler is restarted), or you can use::

    RunPython setup.py install

to install it as an ``.egg`` file.

Note that when installed as an egg file, changes made to the source code will
not affect Chandler execution, until you run ``setup.py install`` or ``setup.py
develop`` again.

After making changes to this plugin, you should update its version number in
``setup.py`` and in the chandler/Makefile, so that people using "quick builds"
of Chandler will use your new version.

If you want to run this plugin's tests use::

    RunPython setup.py test

For more information on the plugin development process, see the original
proposal at:

 http://lists.osafoundation.org/pipermail/chandler-dev/2006-March/005552.html

