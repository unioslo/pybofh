.. highlight:: bash

Developing pybofh
=================

Environment
-----------

Install bofh into a `virtualenv`_ using `pip`_ to test your ongoing
changes::

        % virtualenv ~/venv
        % source ~/venv/bin/activate
        % pip install -e .


Tests
-----

Unit tests live under the ``tests/`` directory and are written using the
`pytest`_ testing framework.  The tests are typically invoked through
`tox`_ to ensure compatibility with supported Python runtimes.

The following are all equal ways to run all the tests on all supported
configurations, and presupposes that you have the necessary Python
runtimes installed::

        % ./setup.py test
        % tox
        % python -m tox

Tests may also be invoked directly with `pytest`_::

        % pytest
        % python -m pytest


Code style
----------

Code style is not strictly enforced, but some general advice applies:

* Write pretty code
* Never use tab indents in Python code
* Follow PEPs to the best of your ability (`PEP-8`_, `PEP-257`_)
* Docstrings should work with `sphinx`_

Apply all the linters.  The author recommends running ``flake8`` with
plugins: ``naming``, ``pycodestyle``, ``pyflakes``.


Contribution guidelines
-----------------------
TODO: Make a ``CONTRIBUTE.rst`` in the root, and include?


.. References
.. ----------
.. _flake-8: http://flake8.pycqa.org/
.. _pep-257: https://www.python.org/dev/peps/pep-0257/
.. _pep-8: https://www.python.org/dev/peps/pep-0008/
.. _pip: https://pip.pypa.io/en/stable/user_guide/
.. _pytest: https://docs.pytest.org/
.. _sphinx: http://www.sphinx-doc.org/
.. _tox: https://tox.readthedocs.io/
.. _virtualenv: https://virtualenv.pypa.io/
