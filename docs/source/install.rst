Installing pybofh
=================

Install from `pypi`_
--------------------

TODO: Make and publish distribution


Install from RPM
----------------

TODO: Make and publish RPM


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
