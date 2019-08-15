pybofh
======

Synopsis
--------

**pybofh** [*options*]


Description
-----------

:program:`pybofh` starts an interactive command line client for communicating with
the Cerebrum XMLRPC server.


Options
-------
.. program:: pybofh

.. option:: -h, --help

   Display usage summary

.. option:: --version

   Display the current :program:`pybofh` version.


.. rubric:: Connection Options

.. option:: --url <url>

   Connect to an XMLRPC server at the given ``<url>``. The default value is the
   ``Cerebrum`` XMLRPC server for the University of Oslo.

.. option:: -u <username>, --user <username>

   Log in to the server using the given ``<username>``. The client will *always*
   prompt for the password before connecting.

.. option:: -c <filename>, --cert <filename>

   When connecting to an HTTPS server, the ca certificates from ``<filename>``
   will be used to validate the server certificate.
   If none of the certificates in ``<filename>`` can be used to validate the
   server certificate, the client will disconnect.

.. option:: --insecure

   By default, the client will require the hostname of the server to be present
   in the server certificate, either as the ``CN`` name, or as a name in a
   X509v3 subjectAltName extension.
   Giving this flag will skip hostname validation, which can be useful for test
   environments.

.. option:: --timeout <seconds>

   Sets a timeout for connections. This will cause the client to abort if no
   connection can be established within ``<seconds>`` seconds.


.. rubric:: Output Options

.. option:: -p <prompt>, --prompt <prompt>

   Sets the interactive prompt for entering commands.

.. option:: -v, --verbosity [debug-level]

   Sets the verbosity for debug output. By default, debug output is disabled.
   Debug output is printed to ``stderr``. The ``-v`` flag can be repeated for
   more verbose output.
