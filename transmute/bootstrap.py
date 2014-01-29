#!/usr/bin/env python
#
#   Copyright 2014 Telenor Digital AS
#
#   Licensed under the Apache License, Version 2.0 (the "License"); you may not
#   use this file except in compliance with the License. You may obtain a copy
#   of the License at
#
#       http://www.apache.org/licenses/LICENSE-2.0
#
#   Unless required by applicable law or agreed to in writing, software
#   distributed under the License is distributed on an "AS IS" BASIS, WITHOUT
#   WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied. See the
#   License for the specific language governing permissions and limitations
#   under the License.

"""Bootstrap installation of transmute package.

When imported (or directly executed), this module will make the latest transmute
package available, downloading it from PyPI as needed. Dowloaded packages are
stored in a local cache and will be reused in subsequent runs.

This can also be used to bootstrap applications that use the transmute package.
In this case, the module becomes the application's main executable. A couple of
customization points are provided to support this use case with minimal effort:

    requirements: global variable listing packages to be fetched from PyPI.
    main(): placeholder for application specific logic. If the module is
        executed as __main__ script, this gets called after packages in
        requirements have been updated and added to sys.path.

Additionally, bootstrap_starting(), bootstrap_succeeded() and bootstrap_failed()
are called at specific points in the bootstrapping process.

The following example could be used to load latest 'foobar' from PyPI and invoke
the foobar.cli.main() entry point:

    requirements = [ 'foobar' ]
    def main():
        import foobar.cli
        return foobar.cli.main()

"""


################################################################################
# Customization points to support running module as main application script.
################################################################################

requirements = [ 'transmute' ]

def main():
    """Called when module is '__main__', after successful bootstrap."""
    ### ~~~ Your code here ~~~ ###

def bootstrap_starting():
    """Called before attempting to load/download packages."""

def bootstrap_succeeded():
    """Called after (updated) packages have been added to sys.path."""
    global _bootstrapped_by_transmute
    _bootstrapped_by_transmute = True

def bootstrap_failed():
    """Called when bootstrap fails to download packages from PyPI or load them
    from the local cache.
    """
    raise RuntimeError("Unable to load 'transmute' package.")


################################################################################
# transmute.bootstrap code follows.
################################################################################

import os
import os.path
import sys

def _chunk_read(file, chunk_size=16*1024):
    """Read file one chunk at a time."""

    while True:
        chunk = file.read(chunk_size)
        if chunk == '':
            break
        yield chunk

def _md5(filename):
    """Compute MD5 hash of a file."""

    import hashlib

    h = hashlib.md5()
    try:
        with open(filename) as file:
            for chunk in _chunk_read(file):
                h.update(chunk)
    except: pass

    return h.hexdigest()

def _copy(source, destination, chunk_size):
    """Read source into destination, one chunk at a time."""

    for chunk in _chunk_read(source, chunk_size):
        destination.write(chunk)

def _download(source, filename, md5sum):
    """Copy source to filename, verify MD5 hash of content.

    Content is initially saved to a temporary file and the content's MD5 hash is
    verified before the file is atomically renamed to the desired filename.

    This will call source.close().
    """
    import contextlib
    import tempfile

    with contextlib.closing(source):
        dirname = os.path.dirname(filename)
        dst = tempfile.NamedTemporaryFile(suffix='.download', dir=dirname)
        with contextlib.closing(dst):
            _copy(source, dst, 4 * 1024)
            dst.flush()

            if _md5(dst.name) != md5sum:
                raise RuntimeError(
                        "MD5 hash of local file doesn't match expected value")

            # Depend on non-documented implementation of NamedTemporaryFile, a
            # shame, but prettier than the alternative
            dst.delete = False

            os.rename(dst.name, filename)

def reset_system_path(working_set):
    """Prepend entries in working_set to sys.path."""

    for entry in sys.path:
        if entry not in working_set.entries:
            working_set.add_entry(entry)

    sys.path[:] = working_set.entries

    if 'pkg_resources' in sys.modules:
    # pkg_resource's global working_set may be outdated
        reload(sys.modules['pkg_resources'])

def require(working_set, baskets, *requirements):
    """Satisfy requirements from given baskets."""

    import pkg_resources
    import zipimport

    requirements = list(pkg_resources.parse_requirements(requirements))

    environment = pkg_resources.Environment()
    for basket in baskets:
        basket.fill_environment(environment, requirements)

    for dist in working_set.resolve(requirements, env=environment):
        if hasattr(dist, '_transmute_basket'):
            dist._transmute_basket.make_local(dist)
            dist._provider = pkg_resources.EggMetadata(
                    zipimport.zipimporter(dist.location))
        working_set.add(dist)


class Basket(object):
    """A container for Python Eggs."""

    _cache_dir = os.path.expanduser('~/.python-transmute/cache')

    def __init__(self, path=None, url=None):
        assert (path is None) != (url is None)

        if path is None:
            path = self._prepare_cache(url)

        self.path = os.path.join(path, '') # Keep trailing separator!
        self.distributions = {}

        try:
            files = os.listdir(self.path)
        except:
            # Ignore missing directory unless it's needed to cache remote
            # packages. A remote basket is unusable without the local cache.
            if url:
                raise
        else:
            self.add(*files)

    def _prepare_cache(self, url):
        import urllib

        path = os.path.join(self._cache_dir, urllib.quote(url, ''))
        if not os.path.isdir(path):
            os.makedirs(path)
        return path

    @classmethod
    def _is_egg(cls, filename):
        return filename[-4] == '.' \
                and filename[-3:].lower() == 'egg'

    def get_distribution(self, egg, **metadata):
        from pkg_resources import Distribution, EGG_DIST

        dist = Distribution.from_location(self.path + egg, egg)
        dist._transmute_basket = self
        dist._transmute_metadata = metadata

        # Prefer local packages.
        dist.precedence = EGG_DIST - 0.1

        return dist

    def add(self, *eggs, **metadata):
        for egg in eggs:
            if not self._is_egg(egg):
                continue
            self.distributions[egg] = self.get_distribution(egg, **metadata)

    def fill_environment(self, environment, requirements=None):
        for dist in self.distributions.itervalues():
            environment.add(dist)

    def fetch(self, dist, **metadata):
        pass

    def make_local(self, dist):
        if not os.path.isfile(dist.location):
            self.fetch(dist, **dist._transmute_metadata)


class PyPIBasket(Basket):
    """A proxy basket for eggs available in PyPI."""

    pypi_url = 'https://pypi.python.org/pypi'
    _distributions = {}

    def __init__(self):
        super(PyPIBasket, self).__init__(url=self.pypi_url)

    def fetch(self, dist, **metadata):
        import urllib2

        _download(urllib2.urlopen(metadata['url']),
                dist.location, metadata['md5_digest'])

    def _add_packages(self, project_name, environment):
        import contextlib
        import json
        import urllib2

        if project_name not in self._distributions:
            url = '%s/%s/json' % (self.pypi_url, project_name)
            with contextlib.closing(urllib2.urlopen(url)) as req:
                metadata = json.load(req)

            distributions = []
            for package in metadata['urls']:
                if not sys.version.startswith(package['python_version']) \
                        or package['packagetype'] != 'bdist_egg':
                    continue
                distributions.append(
                        self.get_distribution(package['filename'], **package))

            self._distributions[project_name] = distributions

        for dist in self._distributions[project_name]:
            environment.add(dist)

    def fill_environment(self, environment, requirements=None):
        super(PyPIBasket, self).fill_environment(environment, requirements)

        for req in requirements:
            try: self._add_packages(req.project_name, environment)
            except: raise

PYPI_BASKET = PyPIBasket()


def bootstrap():
    """Bootstrap 'transmute' package, making it available for import.

    Actual packages to be bootstrapped are defined in the global variable
    requirements.

    Latest packages are downloaded from PyPI, if available, and added to
    sys.path.
    """
    bootstrap_starting()

    import pkg_resources
    working_set = pkg_resources.WorkingSet([])

    try: # Fetch latest packages from PyPI
        require(working_set, [ PYPI_BASKET ], *requirements)
    except:
        try: # Use previously downloaded packages, if download fails
            require(working_set, [ Basket(url=PyPIBasket.pypi_url) ],
                    *requirements)
        except:
            bootstrap_failed()
            return

    reset_system_path(working_set)
    bootstrap_succeeded()

def _clean_namespace():
    """Clean module's namespace.

    Used prior to a reload() of the module when the present module is used to
    bootstrap the Real Thing (tm).
    """
    global __doc__, os, sys
    del __doc__
    del os
    del sys

    global requirements, main, bootstrap_starting, bootstrap_succeeded, \
            bootstrap_failed
    del requirements
    del main
    del bootstrap_starting
    del bootstrap_succeeded
    del bootstrap_failed

    global _chunk_read, _md5, _copy, _download
    del _chunk_read
    del _md5
    del _copy
    del _download

    global reset_system_path, require, Basket, PyPIBasket, PYPI_BASKET
    del reset_system_path
    del require
    del Basket
    del PyPIBasket
    del PYPI_BASKET

    global bootstrap, _clean_namespace
    del bootstrap
    del _clean_namespace


if __name__ in requirements:
    bootstrap()

    # Module is filling in for a package so cleanup namespace and reload
    _clean_namespace()

    import sys
    reload(sys.modules[__name__])
else:
    import importlib
    try:
        for package in requirements:
            importlib.import_module(package)
    except ImportError:
        bootstrap()


# Running as self-contained script, invoke user hook.
if __name__ == '__main__':
    sys.exit(main())
