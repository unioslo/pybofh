Installing bofh
===============
There are several ways to obtain bofh.  If you are an end-user and run
RHEL or Fedora you likely want the RPM package.  If you’re an end-user
on any other system you should consider installing the Python package
from PyPI.  If you intend on developing or making local changes to bofh,
you may also install it directly from source.


Install with pip
-----------------
bofh is available off the central Python package index `PyPI`_.
It can be installed and upgraded this way:
::

    % pip install --upgrade bofh

We also publish a source distribution in the internal *int-pypi* repository
at `<https://int-pypi.uio.no/>`_:
::

   % pip install \
       --upgrade \
       --extra-index-url https://int-pypi.uio.no/simple \
       bofh


Install from RPM
----------------
At the University of Oslo, bofh is available from `<https://rpm.uio.no>`_ as the
``python3-bofh`` package:
::

   % dnf install python3-bofh


Install from source
-------------------
You are encouraged to install bofh into a `virtualenv`_ to avoid package
conflicts and other issues with your system’s Python environment:
::

   % virtualenv /path/to/bofh-env
   % source /path/to/bofh-env/bin/activate

Install bofh using ``pip``:
::

   % /path/to/bofh-env/bin/pip install /path/to/bofh-source

Use bofh either by activating the virtualenv environment:
::

   % source /path/to/bofh-env/bin/activate
   % pybofh --help

Or symlink the ``bofh`` script from your virtual environment to somewhere
on your ``$PATH``:
::

   % cd ~./local/bin
   % ln -s /path/to/bofh-env/bin/pybofh


.. _virtualenv: https://virtualenv.pypa.io/en/stable/
.. _PyPI: https://pypi.org/
