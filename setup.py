"""Runs basic linting for repository."""

import sys
from distutils.cmd import Command
from pathlib import Path

from setuptools import find_packages
from setuptools import setup

PRODUCTION_PACKAGES = ('nile',)


class _BaseCommand(Command):
    """Base command for all other commands."""

    user_options = []  # type: ignore

    root_dir = Path(__file__).parent

    @property
    def test_paths(self):
        """Produces modules to run through automated testing/linting."""
        for module in PRODUCTION_PACKAGES:
            yield str(self.root_dir / module)
        yield __file__

    def initialize_options(self):
        pass

    def finalize_options(self):
        pass

    def _run(self, path):
        raise NotImplementedError

    def run(self):
        for test_path in self.test_paths:
            self._run(test_path)


class Pylint(_BaseCommand):
    """Pylint command."""

    description = 'Run pylint on source files'

    def _run(self, path):
        from pylint.lint import Run
        args = [path]
        rcfile = self.root_dir / '.pylintrc'
        if rcfile.is_file():
            args.append('--rcfile={}'.format(rcfile))
        error = Run(args, do_exit=False).linter.msg_status
        if error:
            sys.exit(error)


class Mypy(_BaseCommand):
    """Mypy command."""

    description = 'Run mypy on source files'

    def _run(self, path):
        from mypy.main import main
        main(None, [path])


with open('README.md', 'r', encoding='utf-8') as fh:
    LONG_DESCRIPTION = fh.read().strip()

with open('version.txt', 'r', encoding='utf-8') as fh:
    VERSION = fh.read().strip()

with open('requirements.txt', 'r', encoding='utf-8') as fh:
    REQUIREMENTS = [line.strip() for line in fh]

with open('requirements-dev.txt', 'r', encoding='utf-8') as fh:
    REQUIREMENTS_DEV = [line.strip() for line in fh]

if sys.version_info[:2] <= (3, 4):
    REQUIREMENTS.append('typing')

setup(
    name='nile',
    version=VERSION,
    author='Nick Iodice, Erik Schlegel',
    author_email='niiodice@microsoft.com',
    description='Integration test harness useful for distributed deployments',
    long_description=LONG_DESCRIPTION,
    long_description_content_type='text/markdown',
    url='https://github.com/Microsoft/nile',
    packages=find_packages(),
    classifiers=[
        'Programming Language :: Python :: 3',
        'Programming Language :: Python :: 3.4',
        'Programming Language :: Python :: 3.5',
        'Programming Language :: Python :: 3.6',
        'Programming Language :: Python :: 3.7',
        'License :: OSI Approved :: MIT License',
        'Operating System :: OS Independent',
    ],
    python_requires='>=3.2.*',
    setup_requires=['pytest-runner'],
    tests_require=['pytest'],
    install_requires=REQUIREMENTS,
    extras_require={
        'dev': REQUIREMENTS_DEV,
    },
    cmdclass={
        'pylint': Pylint,
        'mypy': Mypy,
    },
)
