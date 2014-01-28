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

try: from transmute._version import __version__
except ImportError: __version__ = 'unknown'

import transmute.basket
from transmute.bootstrap import PYPI_BASKET
from transmute.resolver import Resolver
from transmute.transmuter import Transmuter

PYPI_SOURCE = PYPI_BASKET
transmute.basket.register_basket(PYPI_BASKET.pypi_url, PYPI_BASKET)

_resolver = Resolver()
add_source = _resolver.add_source
require = _resolver.require
reset = _resolver.reset

def update(resolver=None):
    if resolver is None:
        resolver = globals()['_resolver']
    tm = Transmuter(resolver.working_set)
    tm.transmute()
