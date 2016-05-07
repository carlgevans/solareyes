#!/usr/bin/env python
#
# Copyright 2016 Carl Evans
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#     http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.

import json
import requests
import ssl
from datetime import datetime


"""A library for interacting with the SolarWinds API.

To begin using this library, instantiate an object from the class named Api with the constructor arguments api_url,
username & password.

E.g.: sw_api = solarwinds.Api("nms.company.com", "myusername", "mypassword")
"""
__author__ = "Carl Evans"
__copyright__ = "Copyright 2016 Carl Evans"
__license__ = "Apache 2.0"
__title__ = "SolarWinds"
__version__ = "1.0"


class Api(object):
    """SolarWinds API class.

    Contains all of the relevant API functions for SolarWinds.

    Attributes:
        api_hostname: A string containing the appropriate API url.
        username: A string containing the SolarWinds username.
        password: A string containing the SolarWinds password.
    """
    def __init__(self, api_hostname=None, username=None, password=None):
            self.api_hostname = api_hostname
            self.username = username
            self.password = password

    def status(self):
        return True

    def get_path_nodes(self):

        swis = SwisClient(self.api_hostname, self.username, self.password)

        print("SWIS URL: " + swis.url)
        print(ssl.OPENSSL_VERSION)
        print("Query Test:")
        results = swis.query("SELECT Uri FROM Orion.Nodes WHERE NodeID=@id", id=1042)
        uri = results['results'][0]['Uri']
        print(uri)


def _json_serial(obj):
    """JSON serializer for objects not serializable by default json code"""
    if isinstance(obj, datetime):
        serial = obj.isoformat()
        return serial


class SwisClient:
    def __init__(self, api_hostname, username, password):
        self.url = "https://%s:17778/SolarWinds/InformationService/v3/Json/" % api_hostname
        self.credentials = (username, password)

    def query(self, query, **params):
        return self._req(
                "POST",
                "Query",
                {'query': query, 'parameters': params}).json()

    def invoke(self, entity, verb, *args):
        return self._req(
                "POST",
                "Invoke/{}/{}".format(entity, verb), args).json()

    def create(self, entity, **properties):
        return self._req(
                "POST",
                "Create/" + entity, properties).json()

    def read(self, uri):
        return self._req("GET", uri).json()

    def update(self, uri, **properties):
        self._req("POST", uri, properties)

    def delete(self, uri):
        self._req("DELETE", uri)

    def _req(self, method, frag, data=None):
        return requests.request(method, self.url + frag,
                                data=json.dumps(data, default=_json_serial),
                                verify=False,
                                auth=self.credentials,
                                headers={'Content-Type': 'application/json'})

