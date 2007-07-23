This plugin is just an example to show how minimal a plugin project can be.
It doesn't actually do anything, but is a complete example with a setup
script and tests.

To download and install the plugin from the Chandler UI, 
use the "Plugins -> Download" and "Plugins -> Install" menus.

To download and install the plugin from the command line, use Chandler's
InstallPlugin script and restart Chandler::

    InstallPlugin Chandler-HelloWorldPlugin

If you want to experiment with its code, you can use::

    RunPython setup.py develop

to install it in development mode (where you can make changes and have them
take effect whenever Chandler is restarted), or you can use::

    RunPython setup.py install

to install it as an ``.egg`` file.

Note that when installed as an egg file, changes made to the source code will
not affect Chandler execution, until you run ``setup.py install`` or ``setup.py
develop`` again.

If you want to run this plugin's tests (which also don't do anything), use::

    RunPython setup.py test

The only thing this plugin actually does when Chandler is run, is to write an
entry to the log file when it is first loaded.  The entry will appear only if
the parcel has just been installed in a fresh repository, or if it is the first
time running a new or changed version of the parcel.

For more information on this plugin and the plugin development process, see
the original proposal at:

 http://lists.osafoundation.org/pipermail/chandler-dev/2006-March/005552.html

The svn sources for this plugin are at:

 http://svn.osafoundation.org/chandler/trunk/chandler/projects/Chandler-HelloWorldPlugin#egg=Chandler_HelloWorldPlugin-dev

and can be retrieved with::

    RunPython -m easy_install --editable -b . Chandler_HelloWorldPlugin==dev
