# pybofh

*pybofh* is an interactive XMLRPC client for a `Cerebrum.modules.bofhd`
server. If you don't know what [Cerebrum][crb_about] is, you probably don't
want this.

*pybofh* should run on Python 2.7 (>= 2.7.9, >= RHEL7 2.7.5), and Python 3.6 or newer.


## Install

We recommend that you use [virtualenv][virtualenv] to install *pybofh*.

```bash
python setup.py install
```


## Use

```bash
pybofh --help
python -m bofh --help
```


## Documentation

You'll have to build the *pybofh* documentation yourself (for now).

Documentation is built using *sphinx*, and build requirements are specified in
the [docs/requirements.txt](docs/requirements.txt) file.

```bash
python2 setup.py build_sphinx -b html
cd build/sphinx/html
python3 -m http.server
```
Then go to <http://localhost:8000/>.

There is also also a troff man-page for the *bofh* script, which can be built
with:

```bash
python2 setup.py build_sphinx -b man
man ./build/sphinx/man/bofh.1
```

For other documentation formats, see [docs/README.md](docs/README.md) and
[docs/Makefile](docs/Makefile).


## Module usage

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

  [crb_about]: https://www.usit.uio.no/om/tjenestegrupper/cerebrum/
  [crb_src]: https://bitbucket.usit.uio.no/projects/CRB/repos/cerebrum/
  [virtualenv]: https://virtualenv.pypa.io/
