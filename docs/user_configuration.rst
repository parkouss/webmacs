User configuration
==================

**webmacs** can be configured by writing Python code. The files should lives in
a ~/.webmacs/init directory, starting with an _\_init_\_.py file.

If this file exists, it will be loaded early in the application.

Note you have the full power of Python in there, and as it is loaded early you
can change and adapt nearly everything of the webmacs behavior.

.. note::

   Only the documented functions and objects here are considered stable (meaning
   it won't change without change notes and explanations). The other api you can
   use is considered internal and might change without notification.


The init function
*****************

You can write a function **init** that would be called when webmacs is about to
start. This function must takes one parameter (usually named *opts*), that
contains the result of the parsed command line. For now, there is only one
useful parameter:

- opts.url:  the url given in the command line, or None

Overriding the init function does override the default init function of webmacs,
though it is still accessible with :func:`webmacs.main.init`. Hello world
example:

.. code-block:: python

   import webmacs.main


   def init(opts):
       print("hello wordl")
       if opts.url:
           print("{} was given as a command line argument".format(opts.url))
       webmacs.main.init(opts)


The default webmacs.main.init function is responsible restoring the session, or
opening the given url for example.


.. note::

   It is not required to create an init function in the user configuration
   _\_init_\_.py file. Only do so if you want to change the default webmacs
   initialization. Other changes can be applied early, directly at the module
   level, such as defining **webjumps**.
