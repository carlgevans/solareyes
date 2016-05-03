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

import requests
import errors

"""A library for interacting with the SolarWinds API.

To begin using this library, instantiate an object from class Api with the constructor arguments api_url,
username & password.

E.g.: sw_api = solarwinds.Api("https://nms.company.com", "myusername", "mypassword")
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
        api_url: A string containing the appropriate API url.
        username: A string containing the SolarWinds username.
        password: A string containing the SolarWinds password.
    """
    def __init__(self, api_url=None, username=None, password=None):
            self.api_url = api_url
            self.username = username
            self.password = password

    def status(self):
        return True

