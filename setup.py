#!/usr/bin/env python
# -*- coding: utf-8 -*-

# Copyright 2010 University of Oslo, Norway
#
# This file is part of PyBofh.
#
# PyBofh is free software; you can redistribute it and/or modify it
# under the terms of the GNU General Public License as published by
# the Free Software Foundation, either version 3 of the License, or
# (at your option) any later version.
#
# PyBofh is distributed in the hope that it will be useful, but
# WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the GNU
# General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with PyBofh; if not, write to the Free Software Foundation,
# Inc., 59 Temple Place, Suite 330, Boston, MA 02111-1307, USA.

from distutils.core import setup
from distutils.cmd import Command

class archival(object):
    def __init__(self):
        self.latesttag = []
        self.tag = []
        self.latesttagdistance = -1
        self.repo = self.node = self.branch = None
        input = None
        try:
            input = open(".hg_archival.txt", "r")
            self.parse_archival(input)
        except IOError:
            pass
        finally:
            if input is not None:
                input.close()

    def parse_archival(self, input):
        for k, v in [x.split(":", 1) for x in  input.readlines()]:
            if k in ('repo', 'node', 'branch'):
                setattr(self, k, v.strip())
            elif k == 'tag':
                self.tag.append(v.strip())
            elif k == 'latesttag':
                self.latesttag.append(v.strip())
            elif k == 'latesttagdistance':
                self.latesttagdistance = int(v.strip())

def archive_version():
    ar = archival()
    for tag in ar.tag:
        if tag.startswith('version-'):
            return tag.split('-', 1)[1]
    if ar.node:
        return ar.node[:12]

def hg_version():
    import os
    import mercurial.ui
    import mercurial.localrepo
    ui = mercurial.ui.ui()
    repo = mercurial.localrepo.localrepository(ui, os.getcwd())
    ctx = repo['.']
    for tag in ctx.tags():
        if tag.startswith('version-'):
            return tag.split('-', 1)[1]
    return ctx.hex()[:12]

def bofh_version():
    from bofh.version import version
    return version

def get_version():
    av = archive_version()
    if av:
        return av
    try:
        hv = hg_version()
        return hv
    except:
        return bofh_version()



def replace_copy_file(version):
    old = Command.copy_file

    def write_content(fname):
        f = open(fname, "w")
        f.write('version = %r' % version)
        f.close()

    def copy_file (self, infile, outfile,
        preserve_mode=1, preserve_times=1, link=None, level=1):
        """Copy a file respecting verbose, dry-run and force flags.  (The
        former two default to whatever is in the Distribution object, and
        the latter defaults to false for commands that don't define it.)"""

        if infile.endswith("version.py"):
            if self.dry_run:
                return outfile, 1
            try:
                self.make_file([infile], outfile, write_content, (outfile,), level=level)
            except IOError:
                return outfile, 0
            return outfile, 1

        return old(self, infile, outfile, preserve_mode, preserve_times, link, level)

    Command.copy_file = copy_file

version = get_version()
replace_copy_file(unicode(version))

setup(name='pybofh',
      description='Cerebrum Bofh client',
      version=version,
      license='GPL',
      scripts=['scripts/bofh', 'scripts/passwd'],
      packages=['bofh'])

