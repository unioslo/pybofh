from __future__ import unicode_literals

from bofh.parser import Command


def test_command_init(bofh):
    line = 'group_name command_name'
    cmd = Command(bofh, line)

    assert cmd.bofh is bofh
    assert cmd.line == line
