.. highlight:: bash

Developing bofh
===============

Environment
-----------
Install bofh into a `virtualenv`_ using `pip`_ to test your ongoing
changes:
::

    % virtualenv ~/venv
    % source ~/venv/bin/activate
    % pip install -e .[dev]


Tests
-----
Unit tests live under the ``tests/`` directory and are written using the
`pytest`_ testing framework.

Tests may also be invoked directly with `pytest`_:
::

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


Releasing
---------
To prepare a new release of bofh you should first ensure all tests are
passing:
::

    % python -m pytest

Before releasing any changes, the version number needs to be updated.  Please
pick a good, new version according to *semantic versioning* principles:
::

    % # bump patch version (i.e. 1.5.0 to 1.5.1), commit, and tag
    % bumpversion patch  # or minor, or major

If you're unsure, do some dry-runs and testing:
::

    % # Only show what changes *would* be done:
    % bumpversion minor --dry-run --verbose

    % # Only do changes in the working tree - no git interactions
    % bumpversion minor --no-commit --no-tags


This will:

 1. Write a new version number to the ``bofh.metadata`` module
 2. Update bumpversion metadata in ``setup.cfg``
 3. Commit these changes to the repository
 4. Tag this commit with a new version tag

Then we publish the source code:
::

    % git push
    % git push --tags

And upload the package to `PyPI`_:
::

    % git checkout vX.Y.Z
    % python -m build
    % python -m twine upload … dist/*


Contribution guidelines
-----------------------
TODO: Make a ``CONTRIBUTE.rst`` in the root, and include?


.. References
.. ----------
.. _flake-8: http://flake8.pycqa.org/
.. _pep-257: https://www.python.org/dev/peps/pep-0257/
.. _pep-8: https://www.python.org/dev/peps/pep-0008/
.. _pip: https://pip.pypa.io/en/stable/user_guide/
.. _PyPI: https://pypi.org/project/bofh/
.. _pytest: https://docs.pytest.org/
.. _sphinx: http://www.sphinx-doc.org/
.. _virtualenv: https://virtualenv.pypa.io/
