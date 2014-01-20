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

import os
import os.path
import re

_basket_factory = {}
_basket = {}

_SCHEME_REGEX = re.compile("^[a-z][a-z0-9+.-]*$")
def register_basket_factory(scheme, factory):
    assert _SCHEME_REGEX.match(scheme)
    _basket_factory[scheme] = factory

_EGG_REGEX = re.compile("\.egg$", re.IGNORECASE)
def _is_egg(filename):
    return _EGG_REGEX.search(filename)

class Basket:
    def __init__(self, path=None, eggs=None):
        self.path = path
        self.eggs = set()

        if eggs:
            self.add(eggs)

    def add(self, eggs):
        self.eggs |= set(filter(_is_egg, eggs))

    def get_local_path(self, egg):
        assert egg in self.eggs
        return os.path.join(self.path, egg)

    def fetch(self, egg):
        return self.get_local_path(egg)

def _get_basket(url):
    scheme, colon, _ = url.partition(':')
    if colon == ':' \
            and scheme in _basket_factory:
        return _basket_factory[scheme](url)

    # Assume url is a local path
    return Basket(url, os.listdir(url))

def get_basket(url):
    if url not in _basket:
        try: _basket[url] = _get_basket(url)
        except: pass
    return _basket.get(url, Basket())
