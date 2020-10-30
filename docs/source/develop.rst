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


Unit tests
----------

* Unit tests live under the ``tests/`` directory
* Tests run using `pytest`_, typically invoked using `tox`_

::

   # Run tests using tox
   tox
   python -m tox

   # Run tests using pytest
   pytest
   python -m pytest

   # Run tests using our custom setuptools command
   python setup.py test


Unit tests may be written as :py:mod:`unittest.TestCase` classes, but functional
pytest tests are preferred.


Codestyle
---------
Codestyle is not strictly enforced.

* Write pretty code
* Never use tab indents in python code
* Follow PEPs to the best of your ability (`PEP-8`_, `PEP-257`_)
* Docstrings should work with `sphinx`_

Apply all the linters. The author recommends running ``flake8`` with plugins:
``naming``, ``pycodestyle``, ``pyflakes``.


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
