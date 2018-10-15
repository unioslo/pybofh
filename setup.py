#!/usr/bin/env python
# -*- coding: utf-8 -*-
#
# Copyright 2010-2018 University of Oslo, Norway
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
import io
import sys

import setuptools
import setuptools.command.test


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


class PyTest(setuptools.command.test.test):
    """ Run tests using pytest.

    From `http://doc.pytest.org/en/latest/goodpractices.html`.

    """

    user_options = [('pytest-args=', 'a', "Arguments to pass to pytest")]

    def initialize_options(self):
        super().initialize_options()
        self.pytest_args = []

    def run_tests(self):
        import shlex
        import pytest
        args = self.pytest_args
        if args:
            args = shlex.split(args)
        errno = pytest.main(args)
        raise SystemExit(errno)


def main():
    setup_requirements = ['setuptools_scm']
    test_requirements = list(get_requirements('requirements-test.txt'))
    install_requirements = list(get_requirements('requirements.txt'))

    if {'build_sphinx', 'upload_docs'}.intersection(sys.argv):
        # Sphinx modules:
        setup_requirements.extend(get_requirements('docs/requirements.txt'))
        # pofh-dependencies for generating autodoc:
        setup_requirements.extend(get_requirements('requirements.txt'))

    setuptools.setup(
        name='pybofh',
        description='Cerebrum Bofh client',
        long_description=get_textfile('README.md'),
        long_description_content_type='text/markdown',

        url='https://bitbucket.usit.uio.no/projects/CRB/repos/pybofh',
        author='USIT, University of Oslo',
        author_email='bnt-int@usit.uio.no',
        license='GPLv3',

        use_scm_version=True,

        setup_requires=setup_requirements,
        install_requires=install_requirements,
        tests_require=test_requirements,

        packages=get_packages(),
        package_data={'bofh.ext': ['LICENCE.txt', 'README.md'], },
        data_files=[('share/pybofh', ['data/cacerts.pem', ]), ],
        entry_points={
            'console_scripts': [
                'bofh = bofh.cli:main',
                'pybofh = bofh.cli:main',
            ],
        },
        classifiers=[
            'Development Status :: 4 - Beta',
            'Environment :: Console',
            'Intended Audience :: System Administrators',
            'License :: OSI Approved :: GNU General Public License v3',
            'Programming Language :: Python :: 2 :: Only',
            'Programming Language :: Python :: 2.6',
            'Programming Language :: Python :: 2.7',
            'Topic :: Software Development :: Libraries',
            'Topic :: System :: Systems Administration',
        ],
        keywords='cerebrum xmlrpc client',
    )


if __name__ == '__main__':
    main()
