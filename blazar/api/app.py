# Copyright (c) 2017 NTT Inc.
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#    http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or
# implied.
# See the License for the specific language governing permissions and
# limitations under the License.

import json

from blazar.api.v1 import app as v1_app
from blazar.api.v2 import app as v2_app


class VersionSelectorApplication(object):
    """Maps WSGI versioned apps and defines default WSGI app."""

    def __init__(self):
        self._status = ''
        self._response_headers = []
        self.v1 = v1_app.make_app()
        self.v2 = v2_app.make_app()

    def _append_versions_from_app(self, versions, app, environ):
        tmp_versions = app(environ, self.internal_start_response)
        if self._status.startswith("300"):
            tmp_versions = json.loads("".join(tmp_versions))
            versions['versions'].extend(tmp_versions['versions'])

    def internal_start_response(self, status, response_headers, exc_info=None):
        self._status = status
        self._response_headers = response_headers

    def __call__(self, environ, start_response):
        self._status = ''
        self._response_headers = []

        if environ['PATH_INFO'] == '/' or environ['PATH_INFO'] == '/versions':
            versions = {'versions': []}
            self._append_versions_from_app(versions, self.v1, environ)
            self._append_versions_from_app(versions, self.v2, environ)
            if len(versions['versions']):
                start_response("300 Multiple Choices",
                               [("Content-Type", "application/json")])
                return [json.dumps(versions)]
            else:
                start_response("204 No Content", [])
                return []
        else:
            if environ['PATH_INFO'].startswith('/v1'):
                return self.v1(environ, start_response)
            return self.v2(environ, start_response)