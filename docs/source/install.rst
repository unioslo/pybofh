Installing pybofh
=================

Install with pip
----------------
For now, a source distribution is published in the *pypi-usit-int* repo at
repo.usit.uio.no. This distribution can be installed and upgraded with:

::

   pip install \
      --upgrade \
      --extra-index-url https://repo.usit.uio.no/nexus/repository/pypi-usit-int/simple \
      pybofh

This source distribution may be extended or replaced with wheels or other binary
distributions at some point.

.. TODO: Do we want to publish 


Install from RPM
----------------
TODO: Make and publish RPM
.. See https://bitbucket.usit.uio.no/users/fhl/repos/python-pybofh-spec/browse


Install from source
-------------------

Install in a `virtualenv`_ to avoid conflicts and other issues with your
operating system python environment:

::

   virtualenv /path/to/my_pybofh_env
   source /path/to/my_pybofh_env/bin/activate

Install pybofh by running the included ``setup.py`` script:

::

   cd /path/to/pybofh_source
   python setup.py install


Use pybofh either by activating the virtualenv environment:

::

   source my_pybofh_env/bin/activate
   bofh --help


Or symlink the ``bofh`` script from your virtual environment to somewhere on
your ``$PATH``.


::

   # Assuming ~/.local/bin is on your $PATH
   cd ~/.local/bin
   ln -s /path/to/my_pybofh_env/bin/bofh
   bofh --help


.. _virtualenv: https://virtualenv.pypa.io/en/stable/
.. _pypi: https://pypi.org/
