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

import pkg_resources
import transmute.basket
import transmute.bootstrap

class Resolver:
    """Find and manage lists of updated packages."""

    def __init__(self, requirements=None, sources=None):
        """Initialize a new Resolver object.

        requirements: string or list of strings listing package requirements.
        """
        self.baskets = []
        self.reset()

        if sources:
            self.add_source(*sources)
        if requirements:
            self.require(requirements)

    def reset(self):
        self.working_set = pkg_resources.WorkingSet([])

    @classmethod
    def _get_basket(cls, source):
        if isinstance(source, basestring):
            return transmute.basket.get_basket(source)
        return source

    @classmethod
    def _get_baskets(cls, *sources):
        return [ cls._get_basket(s) for s in sources ]

    def add_source(self, *sources):
        self.extend(self._get_baskets(sources))

    def require(self, requirements, sources=None):
        baskets = self.baskets
        if sources:
            # Make a copy
            baskets = baskets + self._get_baskets(*sources)

        transmute.bootstrap.require(self.working_set, baskets, *requirements)
