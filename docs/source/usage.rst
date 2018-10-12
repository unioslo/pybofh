Using pybofh
============

This document describes how to use pybofh from the command line. For module
usage, see :doc:`modules/index`.


bofh
----

::

   usage: pybofh [-h] [--version] [--url URL] [-u USER] [-c PEM] [--insecure]
                 [--timeout N] [-p PROMPT] [-v]


connection settings
~~~~~~~~~~~~~~~~~~~
Change what XMLRPC server to connect to, and connection settings.

``--url <url>``
   Connect to an XMLRPC server at the given ``<url>``. The default value is the
   ``Cerebrum`` XMLRPC server for the University of Oslo.

``-u <username>``, ``--user <username>``
   Log in to the server using the given ``<username>``. The client will *always*
   prompt for the password before connecting.

``-c <filename>``, ``--cert <filename>``
   When connecting to an HTTPS server, the ca certificates from ``<filename>``
   will be used to validate the server certificate.
   If none of the certificates in ``<filename>`` can be used to validate the
   server certificate, the client will disconnect.

``--insecure``
   By default, the client will require the hostname of the server to be present
   in the server certificate, either as the ``CN`` name, or as a name in a
   X509v3 subjectAltName extension.
   Giving this flag will skip hostname validation, which can be useful for test
   environments.

``--timeout <seconds>``
   Sets a timeout for connections. This will cause the client to abort if no
   connection can be established within ``<seconds>`` seconds.


output settings
~~~~~~~~~~~~~~~

``-p <prompt>``, ``--prompt <prompt>``
   Sets the interactive prompt for entering commands.

``-v``, ``--verbosity [debug-level]``
   Sets the verbosity for debug output. By default, debug output is disabled.
   Debug output is printed to ``stderr``. The ``-v`` flag can be repeated for
   more verbose output.
