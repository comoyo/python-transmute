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

import re
from transmute.bootstrap import Basket

_basket_factory = {}
_basket = {}

_SCHEME_REGEX = re.compile("^[a-z][a-z0-9+.-]*$")
def register_basket_factory(scheme, factory):
    assert _SCHEME_REGEX.match(scheme)
    _basket_factory[scheme] = factory

def register_basket(url, basket):
    _basket[url] = basket

def _get_basket(url):
    scheme, colon, _ = url.partition(':')
    if colon \
            and scheme in _basket_factory:
        return _basket_factory[scheme](url)

    # Assume url is a local path
    return Basket(path=url)

def get_basket(url):
    if url not in _basket:
        _basket[url] = _get_basket(url)
    return _basket[url]
