Installing bofh
===============

There are several ways to obtain bofh.  If you are an end-user and run
RHEL or Fedora you likely want the RPM package.  If you’re an end-user
on any other system you should consider installing the Python package
from PyPI.  If you intend on developing or making local changes to bofh,
you may also install it directly from source.


Install with pip
----------------

pybofh is available off the central Python package index `PyPI`_.
It can be installed and upgraded this way::

    % pip install --upgrade bofh

We also publish a source distribution in the *pypi-usit-int* repository
at repo.usit.uio.no::

   % pip install \
       --upgrade \
       --extra-index-url https://repo.usit.uio.no/nexus/repository/pypi-usit-int/simple \
       bofh

This source distribution may be extended or replaced with wheels or
other binary distributions at some point.


Install from RPM
----------------
TODO: Make and publish RPM
.. See https://bitbucket.usit.uio.no/users/fhl/repos/python-pybofh-spec/browse


Install from source
-------------------

You are encouraged to install bofh into a `virtualenv`_ to avoid package
conflicts and other issues with your system’s Python environment::

   % virtualenv /path/to/my_pybofh_env
   % source /path/to/my_pybofh_env/bin/activate

Install pybofh by running the included ``setup.py`` script::

   % cd /path/to/pybofh_source
   % python setup.py install

Use bofh either by activating the virtualenv environment::

   % source my_pybofh_env/bin/activate
   % bofh --help

Or symlink the ``bofh`` script from your virtual environment to somewhere
on your ``$PATH``::

   % cd /usr/local/bin/
   % ln -s /path/to/my_pybofh_env/bin/bofh .
   % which bofh
   /usr/local/bin/bofh


.. _virtualenv: https://virtualenv.pypa.io/en/stable/
.. _PyPI: https://pypi.org/
