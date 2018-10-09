# pybofh

*pybofh* is an interactive XMLRPC client for a `Cerebrum.modules.bofhd`
server. If you don't know what [Cerebrum][about_cerebrum] is, you probably don't
want this.


## Install

We recommend that you use [virtualenv][virtualenv] to install *pybofh*.

```bash
python setup.py install
bofh --help
bofh --url https://example.org:8000
```


## Documentation

To read the *pybofh* documentation, you'll have to build it yourself.

```bash
python setup.py sphinx_build
cd build/sphinx/html
python3 -m http.server
```
Then go to <http://localhost:8000/>.

For more documentation build options, see `docs/README.md` and `docs/Makefile`


## Example usage

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
