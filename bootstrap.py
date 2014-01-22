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

# This script can be used to bootstrap installation of an application that uses
# transmute. It can also be used to bootstrap installation and update of the
# transmute module itself.
#
# To bootstrap an application, fill in the main function below to request needed
# packages from transmute and launch the application.
#
# transmute packages are queried/fetched from PyPI and imported prior to calling
# main(). Return values from main() are passed along to sys.exit().

def main():
    ### Your code here?
    pass

# Transmute bootstrap code follows.
def bootstrap_transmute():
    import os
    import os.path
    import sys
    import urllib

    pypi_url = 'https://pypi.python.org/pypi'
    pypi_cache = os.path.expanduser('~/.python-transmute/cache/'
            + urllib.quote(pypi_url, ''))

    os.path.isdir(pypi_cache) \
            or os.makedirs(pypi_cache)

    def md5(path):
        import hashlib

        h = hashlib.md5()
        try:
            with open(path) as f:
                h.update(f.read(16 * 1024))
        except: pass

        return h.hexdigest()

    def download_to(url, filename):
        import contextlib
        import tempfile
        import urllib2

        dirname = os.path.dirname(filename)
        try:
            dst = tempfile.NamedTemporaryFile(dir=dirname, delete=False)
            src = urllib2.urlopen(url)
            while True:
                chunk = src.read(4 * 1024)
                if not chunk:
                    break
                dst.write(chunk)
        except:
            if dst:
                dst.close() # Damn you, Windows!
                os.remove(dst.name)
        else:
            os.rename(dst.name, filename)
        finally:
            if src: src.close()
            if dst: dst.close()

    def get_package_info(package_name):
        import json, urllib2

        url = '%s/%s/json' % (pypi_url, package_name)
        metadata = json.load(urllib2.urlopen(url))

        for info in metadata['urls']:
            if sys.version.startswith(info['python_version']) \
                    and info['packagetype'] == 'bdist_egg':
                return info['url'], info['filename'], info['md5_digest']

        raise RuntimeError(
                "No suitable packages for '%s' in %s" % (package_name, url))

    def get_package(package):
        url, filename, md5sum = get_package_info(package)
        filename = os.path.join(pypi_cache, filename)
        if md5(filename) == md5sum:
            return filename

        download_to(url, filename)
        if md5(filename) == md5sum:
            return filename

        raise RuntimeError('Unable to download package from %s' % url)

    package = get_package('transmute')
    sys.path.insert(0, package)

    if 'transmute' in sys.modules:
        reload(sys.modules['transmute'])
    else:
        import transmute

if __name__ == 'transmute':
    bootstrap_transmute()
else:
    try:
        import transmute
    except ImportError:
        bootstrap_transmute()

if __name__ == '__main__':
    import sys
    sys.exit(main())
