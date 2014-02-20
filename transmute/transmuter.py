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
import transmute.bootstrap

class Transmuter(object):
    """Manage updates to Python's module search path."""

    def __init__(self, entries):
        self.working_set = pkg_resources.WorkingSet(entries)

    @classmethod
    def _get_dist_conflicts(self, dist):
        conflicts = []
        for module in dist._get_metadata('top_level.txt'):
            if module == 'pkg_resources':
                continue
            if module in sys.modules:
                conflicts.append(module)
        return conflicts

    def get_conflicts(self):
        conflicts = {}
        for dist in self.working_set:
            dist_conflicts = self._get_dist_conflicts(dist)
            if dist_conflicts:
                conflicts[dist.project_name] = dist_conflicts
        return conflicts

    def _reset_path(self):
        sys.path[0:0] = self.working_set.entries

    def soft_transmute(self):
        for dist in self.working_set:
            dist.activate()

        self._reset_path()
        reload(pkg_resources)

    def hard_transmute(self):
        self.executable = sys.executable
        self.arguments = [ self.executable ] + sys.argv
        self.environment = os.environ.copy()

        # Reset PYTHONPATH
        self._reset_path()
        self.environment['PYTHONPATH'] = os.pathsep.join(sys.path)

        os.execve(self.executable, self.arguments, self.environment)
        assert False

    def transmute(self):
        """Inject packages in working set."""

        # TODO: Recover from a bad update
        if self.get_conflicts():
            self.hard_transmute()
        else:
            self.soft_transmute()
