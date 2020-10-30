bofh
====

*bofh*, short for *brukerorganisering for hvermannsen*, is a [Cerebrum]
administration tool.

It is an interactive XML/RPC command line client for a
`Cerebrum.modules.bofhd` server.  It is unlikely you want to use this
software unless you know what Cerebrum is.


Install
-------

bofh is implemented in Python and supports Python runtimes 2.7 (>= 2.7.9,
>= RHEL7 2.7.5), and 3.6 or newer.

If you are on RHEL we recommend that you install the bofh RPM package
from the university package repository:

	# dnf install pybofh

On other systems we recommend installing from the official Python package
index (PyPI) into a [virtualenv]:

	% virtualenv ~/venv
	% source ~/venv/bin/activate
	(venv) % pip install bofh


Use
---

	pybofh --help
	python -m bofh --help


Module usage
------------

```python
import bofh
from getpass import getuser, getpass

# Get a client by connecting to bofhd
url = 'https://example.org:8000'
cacert = '/path/to/ca.pem'
client = bofh.connect(url=url, cert=cacert)

# You'll need to authenticate to access restricted commands
client.login(getuser(), getpass())

# Call commands on the client object
try:
    # formatted output
    client.user.info('foo')

    # structured output
    client.run_command('user_info', 'foo')
finally:
    client.logout()
```


Documentation
-------------

You'll have to build the bofh documentation yourself (for now).

Documentation is built using *sphinx*, and build requirements are
specified in the [docs/requirements.txt] file.

	% python setup.py build_sphinx -b html
	% cd build/sphinx/html
	% python3 -m http.server

Then go to http://localhost:8000/.

There is also also a troff man-page for the bofh script, which can be
built with:

	% python setup.py build_sphinx -b man
	% man ./build/sphinx/man/bofh.1

For other documentation formats, see [docs/README.md] and [docs/Makefile].


[Cerebrum]: https://github.com/unioslo/cerebrum
[docs/Makefile]: https://github.com/unioslo/pybofh/blob/master/docs/Makefile
[docs/README.md]: https://github.com/unioslo/pybofh/blob/master/docs/README.md
[docs/requirements.txt]: https://github.com/unioslo/pybofh/blob/master/requirements.txt
[virtualenv]: https://virtualenv.pypa.io/
