# Bofh-client

## Install

We recommend that you use virtualenv:

```bash
virtualenv my_env
source my_env/bin/activate.sh
```

```bash
python setup.py install
bofh --help
bofh --url https://example.org:8000
```


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
    client.user.info('foo')
    client.run_command('user_info', 'foo')
finally:
    client.logout()
```


### `run_command` vs `<group>.<command>`

The `run_command` command returns de-serialized, structured data, as returned by
the XML-RPC server. This is probably what you want to use:

```plain
>>> client.run_command('group_list', 'foo')
[{'expired': None, 'type': u'account', 'id': 42, 'name': u'foo'}]
```

The generated `<group>.<command>` attributes calls
`run_command('<group>_<command>`), and formats the structured output according
to suggestions provided by the XML-RPC server. This is really only useful if
you're building a REPL/interactive client:

```plain
>>> print client.group.list('foo')
Type       Name       Expired
account    foo        <not set>
```


### Errors

Any error from the XML-RPC server is raised as an exception in pybofh:

```plain
>>> client.user.info('does_not_exist')
Traceback (most recent call last):
  File "<stdin>", line 1, in <module>
  File "bofh/proto.py", line 211, in __call__
    ret = self._bofh.run_command(self._fullname, *args)
  File "bofh/proto.py", line 525, in run_command
    return self._run_raw_sess_command("run_command", command, *args)
  File "bofh/proto.py", line 461, in _run_raw_sess_command
    return run_command()
  File "bofh/proto.py", line 459, in run_command
    raise BofhError(msg)
bofh.proto.BofhError: Could not find Account with name=does_not_exist
```

### Timeouts

The `bofh.connect()` method accepts a `timeout` argument. This can be used to
abort from long-running command executions. This however, does not imply that
the command is aborted on the server side, it will run until completion. If the
response of the command is essential, do not set a timeout.

When a timeout occurs, `socket.timeout` will be raised.

```python
import bofh
import socket

client = bofh.connect(url='https://example.org:8000',
                      cert='/path/to/ca.pem',
                      timeout=2)
client.login(getuser(), getpass())

try:
    client.user.history('bootstrap_account')
except socket.timeout:
    print('Ooops. I did it again.')
```
