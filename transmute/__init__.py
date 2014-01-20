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
import pkg_resources
import sys
import transmute.basket
import warnings
import zipimport

class Transmuter:

    _fallback_ws = pkg_resources.WorkingSet([]) # Empty set
    _fallback_env = pkg_resources.Environment() # Provides packages in sys.path

    _path_entries = []

    def __init__(self, requirements=None, sources=None):
        self.reset()

        if sources:
            self.add_source(*sources)
        if requirements:
            self.require(requirements)

    def reset(self):
        self._working_set = pkg_resources.WorkingSet([])
        self._environment = pkg_resources.Environment([])

    @classmethod
    def _get_basket(cls, source):
        return transmute.basket.get_basket(source)

    @classmethod
    def _add_source(cls, environment, source):
        basket = cls._get_basket(source)
        for egg in basket.eggs:
            dist = pkg_resources.Distribution.from_location(source, egg)

            # pkg_resources.Distribution drops the egg name, keeping only its
            # components, while we want to track both source and package name.
            dist._transmute_egg = egg

            environment.add(dist)

    def add_source(self, *sources):
        for source in sources:
            self._add_source(self._environment, source)

    def _get_environment(self, sources):
        if not sources:
            return self._environment

        environment = pkg_resources.Environment([])
        for source in sources:
            self._add_source(environment, source)
        return environment

    def require(self, requirements, sources=None):
        requirements = pkg_resources.parse_requirements(requirements)
        environment = self._get_environment(sources)

        # Find updated packages
        while True:
            try:
                needed = self._working_set.resolve(requirements, environment)
                break
            except pkg_resources.DistributionNotFound as err:
                # Satisfy requirements locally, if can't from sources. This
                # could happen, e.g., if no updates have yet been released.
                for dist in self._fallback_ws.resolve(err.args[:1],
                        self._fallback_env):
                    self._working_set.add(dist)
                continue

        # Double check if updated packages available locally
        for dist in needed:
            requirement = dist.as_requirement()
            try:
                available_locally = self._fallback_ws.resolve([ requirement ],
                        self._fallback_env)
            except pkg_resources.DistributionNotFound:
                basket = self._get_basket(dist.location)
                path = basket.get_local_path(dist._transmute_egg)
                self._working_set.add(dist, entry=path)
            else:
                for local_dist in available_locally:
                    self._working_set.add(local_dist)

    def update(self):
        should_reload = False
        for dist in self._working_set:
            if hasattr(dist, '_transmute_egg'):
                basket = self._get_basket(dist.location)
                filename = basket.fetch(dist._transmute_egg)
                metadata = pkg_resources.EggMetadata(zipimport.zipimporter(filename))
                dist._provider = metadata
                try:
                    with warnings.catch_warnings():
                        warnings.simplefilter('error')
                        dist.check_version_conflict()
                except UserWarning as err:
                    if ' was already imported ' not in err.message:
                        raise
                    should_reload = True

        # TODO: recover from bad updates
        if should_reload:
            self._reload()
            assert False

        self._load()
        self.reset()

    def _append_entries(self, entries):
        for entry in entries:
            if entry not in self._working_set.entries:
                self._working_set.add_entry(entry)

    def _load(self):
        for dist in self._working_set:
            dist.activate()

        self._path_entries.extend(self._working_set.entries)
        self._append_entries(sys.path)
        sys.path[:] = self._working_set.entries

        reload(pkg_resources)

    def _reload(self):
        executable = sys.executable
        arguments = [ sys.executable ] + sys.argv
        environment = os.environ

        self._append_entries(self._path_entries)
        if 'PYTHONPATH' in environment:
            self._append_entries(environment['PYTHONPATH'].split(os.pathsep))
        environment['PYTHONPATH'] = os.pathsep.join(self._working_set.entries)

        os.execve(executable, arguments, environment)

_global_transmuter = Transmuter()

add_source = _global_transmuter.add_source
require = _global_transmuter.require
reset = _global_transmuter.reset
update = _global_transmuter.update
