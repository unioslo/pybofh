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

   Connect to an XMLRPC server at the given ``<url>``.

   The default value is the Cerebrum XMLRPC server for the University of Oslo.
   This default can be changed by setting the environment variable
   ``PYBOFH_DEFAULT_URL``.

.. option:: -u <username>, --user <username>

   Log in to the server using the given ``<username>``.

   The client will *always* prompt for the password before connecting.

.. option:: -c <filename>, --cert <filename>

   Use CA-certificates from ``<filename>``.

   When connecting to an HTTPS server, the ca certificates from ``<filename>``
   will be used to validate the server certificate.  Any CA-certificates or
   revocation lists in the default system CA-path will still be used.

   The default value is a self-signed certificate included with pybofh.  This
   default can be changed by adding a custom ``~/.config/pybofh/cacerts.pem`` or
   by setting the environment variable ``PYBOFH_DEFAULT_CAFILE``.

.. option:: --insecure

   Skip hostname validation.

   By default, the client will require the hostname of the server to be present
   in the server certificate, either as the ``CN`` name, or as a name in a
   X509v3 subjectAltName extension.

.. option:: --timeout <seconds>

   Set a timeout for connections.

   This will cause the client to abort if no connection can be established
   within ``<seconds>`` seconds.


.. rubric:: Output Options

.. option:: -p <prompt>, --prompt <prompt>

   Sets the interactive prompt for entering commands.

.. option:: -v, --verbosity [debug-level]

   Sets the verbosity for debug output.

   By default, all log messages with level ``ERROR`` or above is printed to
   ``stderr``.  Increasing the verbosity will cause more log levels to be
   included in this output.  The ``-v`` flag can be repeated, or the verbosity
   level can be set with ``--verbisity N``, where ``N`` is the desired
   verbosity.

.. option:: -q, --quiet

   Remove all debug output.

   By default, all log messages with level ``ERROR`` or above is printed to
   ``stderr``.  Using this option mute all log messages.  Cannot be used with
   ``-v``.
