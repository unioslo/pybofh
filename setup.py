#!/usr/bin/env python
# -*- coding: utf-8 -*-

# Copyright 2010-2020 University of Oslo
#
# This file is part of pybofh.
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

from __future__ import print_function

import codecs
import io
import os
import shutil
import sys

import setuptools
from setuptools import Command
from setuptools.command.test import test as TestCommand


here = os.path.abspath(os.path.dirname(__file__))
dist = os.path.join(here, "dist")


def mock_mbcs_windows():
    try:
        codecs.lookup('mbcs')
    except LookupError:
        ascii_codec = codecs.lookup('ascii')

        def lookup_func(name, encoding=ascii_codec):
            return {True: encoding}.get(name == 'mbcs')

        codecs.register(lookup_func)


def get_requirements(filename):
    """ Read requirements from file. """
    with io.open(filename, mode='rt', encoding='utf-8') as f:
        for line in f:
            # TODO: Will not work with #egg-info
            requirement = line.partition('#')[0].strip()
            if not requirement:
                continue
            yield requirement


def get_textfile(filename):
    """ Get contents from a text file. """
    with io.open(filename, mode='rt', encoding='utf-8') as f:
        return f.read().lstrip()


def get_packages():
    """ List of (sub)packages to install. """
    return setuptools.find_packages('.', include=('bofh', 'bofh.*'))


class Publish(Command):
    """Support publishing to PyPI via setup.py."""

    description = "Build and publish package."
    user_options = [("repository=", None, "target package index (default: pypi)")]

    def initialize_options(self):
        self.repository = "pypi"

    def finalize_options(self):
        pass

    def run(self):
        if os.path.isdir(dist):
            print("cleaning previous builds")
            shutil.rmtree(dist)

        print("building source distribution")
        execl(sys.executable, "setup.py sdist")

        print("uploading to %s via twine" % self.repository)
        execl("twine", "upload", "--repository", self.repository, "dist/*")

        # TODO(andretol): consider git tagging here


class Tox(TestCommand):
    user_options = [('tox-args=', None, "Arguments to pass to tox")]

    def initialize_options(self):
        TestCommand.initialize_options(self)
        self.tox_args = ''

    def finalize_options(self):
        TestCommand.finalize_options(self)
        self.test_args = []
        self.test_suite = True

    def run_tests(self):
        import tox
        errno = tox.cmdline(args=self.tox_args.split())
        sys.exit(errno)


def main():
    setup_requirements = ['setuptools_scm']
    test_requirements = list(get_requirements('requirements-test.txt'))
    install_requirements = list(get_requirements('requirements.txt'))

    if {'build_sphinx', 'upload_docs'}.intersection(sys.argv):
        setup_requirements.extend(get_requirements('docs/requirements.txt'))
        setup_requirements.extend(get_requirements('requirements.txt'))

    if {'bdist_wininst', }.intersection(sys.argv):
        mock_mbcs_windows()

    setuptools.setup(
        name='pybofh',
        description='Cerebrum bofh client',
        long_description=get_textfile('README.md'),
        long_description_content_type='text/markdown',

        url='https://github.com/unioslo/pybofh',
        author='USIT, University of Oslo',
        author_email='bnt-int@usit.uio.no',
        license='GPLv3',

        use_scm_version=True,

        setup_requires=setup_requirements,
        install_requires=install_requirements,
        tests_require=test_requirements,

        packages=get_packages(),
        package_data={'bofh.ext': ['COPYING', 'README.md'], },
        data_files=[('share/pybofh', ['data/cacerts.pem', ]), ],
        entry_points={
            'console_scripts': [
                'pybofh = bofh.cli:main',
            ],
        },
        classifiers=[
            'Development Status :: 4 - Beta',
            'Environment :: Console',
            'Intended Audience :: System Administrators',
            'License :: OSI Approved :: GNU General Public License v3 (GPLv3)',
            'Programming Language :: Python :: 2.7',
            'Programming Language :: Python :: 3.6',
            'Programming Language :: Python :: 3.7',
            'Programming Language :: Python :: 3.8',
            'Programming Language :: Python :: 3.9',
            'Topic :: Software Development :: Libraries',
            'Topic :: System :: Systems Administration',
        ],
        keywords='cerebrum bofh xmlrpc client',
        cmdclass={
            'test': Tox,
            'publish': Publish,
        },
    )


def execl(path, *args):
    exit_code = os.system("%s %s" % (path, " ".join(args)))
    if exit_code != 0:
        fatal("%s ended with exit code: %s" % (path, exit_code))


def fatal(*args):
    raise SystemExit("error: %s" % " ".join(args))


if __name__ == '__main__':
    main()
