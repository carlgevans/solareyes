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
import json
from datetime import datetime

"""A library for interacting with the ThousandEyes API.

To begin using this library, instantiate an object from class Api with the constructor arguments api_url,
username & password.

E.g.: te_api = thousandeyes.Api("https://api.thousandeyes.com", "myusername", "mypassword")
"""
__author__ = "Carl Evans"
__copyright__ = "Copyright 2016 Carl Evans"
__license__ = "Apache 2.0"
__title__ = "ThousandEyes"
__version__ = "1.0"


class Api(object):
    """ThousandEyes API class.

    Contains all of the relevant API functions for ThousandEyes.

    Attributes:
        api_request: A thousandeyes.ApiRequest instance.
    """
    def __init__(self, api_request=None):
        if api_request is None:
            raise errors.Error("[%s.%s] - You must provide a ThousandEyes APIRequest instance."
                               % (__name__, self.__class__.__name__))
        else:
            self.api_request = api_request

    def status(self):
        """Fetches the current status of the ThousandEyes API.

        Returns:
            A boolean of True if the service is ok and False if not.
        """
        response = self.api_request.get("/status.json")

        if response.status_code == 200:
            return True
        else:
            return False

    def get_network_tests(self):
        """Fetches the current list of network tests from the ThousandEyes API.

        All network tests are returned from Thousand Eyes as Json. The Json response is then split into
        separate tests, decoded and mapped into individual thousandeyes.NetworkTest objects. These objects are then
        added to a list for return to the caller.

        Returns:
            A list of thousandeyes.NetworkTest instances.
        """
        response = self.api_request.get("/tests/network.json")
        tests = json.loads(response.text)
        test_list = []

        for test in tests["test"]:
            # Instantiate a new NetworkTest instance and pass current test for json decoding.
            new_test = NetworkTest()
            new_test.from_json(test)

            # Add the newly populated NetworkTest instance to the list.
            test_list.append(new_test)

        return test_list

    def create_network_test(self, test=None):
        """Creates a new network test on ThousandEyes from the passed instance.

        Args:
            test = A populated thousandeyes.NetworkTest instance.

        Returns:
            A a boolean indicating success (True) or failure (False).
        """
        if test is None:
            raise errors.Error("[%s.%s] - You must provide a ThousandEyes test id to delete."
                               % (__name__, self.__class__.__name__))
        else:
            response = self.api_request.post("/tests/network/new.json", test.to_json())

            if response.status_code == 201:
                return True
            else:
                return False

    def delete_network_test(self, test_id=None):
        """Deletes the specified network test from ThousandEyes.

        Args:
            test_id = The test id that should be deleted.

        Returns:
            A a boolean indicating success (True) or failure (False).
        """
        if test_id is None:
            raise errors.Error("[%s.%s] - You must provide a ThousandEyes test id to delete."
                               % (__name__, self.__class__.__name__))
        else:
            response = self.api_request.delete("/tests/network/%s/delete.json" % test_id)

            if response.status_code == 204:
                return True
            else:
                return False

    def get_agents(self):
        """Fetches the current list of agents from the ThousandEyes API.

        All agents are returned from Thousand Eyes as Json. The Json response is then split into
        separate agents, decoded and mapped into individual thousandeyes.Agent objects. These objects are then
        added to a list for return to the caller.

        Returns:
            A list of thousandeyes.Agent instances.
        """
        response = self.api_request.get("/agents.json")
        agents = json.loads(response.text)
        agent_list = []

        for agent in agents["agents"]:
            # Instantiate a new Agent instance and pass current agent for json decoding.
            new_agent = Agent()
            new_agent.from_json(agent)

            # Add the newly populated Agent instance to the list.
            agent_list.append(new_agent)

        return agent_list


class ApiRequest(object):
    """A wrapper for API calls in order to capture exceptions and various Thousand Eyes status codes.

    Attributes:
        api_url: A string containing the base API url such as https://api.thousandeyes.com.
        auth_email: A string containing the ThousandEyes email address used for authentication.
        auth_token: A string containing the ThousandEyes token used for authentication.
    """
    def __init__(self, api_url, auth_email, auth_token):
        if not api_url or not auth_email or not auth_token:
            raise errors.Error("[%s.%s] - You must provide a ThousandEyes API url, email and auth token."
                               % (__name__, self.__class__.__name__))
        else:
            self.api_url = api_url
            self.auth_email = auth_email
            self.auth_token = auth_token

    def get(self, endpoint):
        """HTTP GET request.

        Args:
            endpoint: A string containing the appropriate endpoint url such as '/status.json'.
        """
        return self._request(0, endpoint)

    def post(self, endpoint, payload):
        """HTTP POST request.

        Args:
            endpoint: A string containing the appropriate endpoint url such as '/status.json'.
            payload: A json encoded payload to post.
        """
        return self._request(1, endpoint, payload)

    def delete(self, endpoint):
        """HTTP DELETE request.

        Args:
            endpoint: A string containing the appropriate endpoint url such as '/status.json'.
        """
        return self._request(2, endpoint)

    def _request(self, _request_type, endpoint, payload=None):
        try:
            if _request_type == 0:
                response = requests.get(self.api_url + endpoint, auth=(self.auth_email, self.auth_token))
                response.raise_for_status()
            elif _request_type == 1:
                headers = {'content-type': 'application/json'}
                response = requests.post(self.api_url + endpoint, auth=(self.auth_email, self.auth_token),
                                         data=payload, headers=headers)
                response.raise_for_status()
            elif _request_type == 2:
                response = requests.delete(self.api_url + endpoint, auth=(self.auth_email, self.auth_token))
                response.raise_for_status()
        except requests.exceptions.HTTPError as e:
            # Thousand Eyes Response Codes.
            if e.response.status_code == 400:
                raise errors.Error("[%s.%s] - ThousandEyes reports a malformed request. Detail: %s"
                                   % (__name__, self.__class__.__name__, e))
            elif e.response.status_code == 401:
                raise errors.Error("[%s.%s] - ThousandEyes reports bad authentication. Detail: %s"
                                   % (__name__, self.__class__.__name__, e))
            elif e.response.status_code == 403:
                raise errors.Error("[%s.%s] - ThousandEyes reports insufficient permissions to execute request. "
                                   "Check ownership and permissions. Detail: %s"
                                   % (__name__, self.__class__.__name__, e))
            elif e.response.status_code == 404:
                # If this is a DELETE operation then don't raise an exception as a 404 just means that it doesn't exist.
                if _request_type == 2:
                    return response
                else:
                    raise errors.Error("[%s.%s] - ThousandEyes reports that the requested endpoint does not exist. "
                                       "Detail: %s" % (__name__, self.__class__.__name__, e))
            elif e.response.status_code == 405:
                raise errors.Error("[%s.%s] - ThousandEyes reports that this endpoint is not accepting the type of "
                                   "request initiated (POSTing to a GET endpoint etc). Detail: %s"
                                   % (__name__, self.__class__.__name__, e))
            elif e.response.status_code == 406:
                raise errors.Error("[%s.%s] - ThousandEyes reports that the content type of the data does not match "
                                   "the accept header of the request. Detail: %s"
                                   % (__name__, self.__class__.__name__, e))
            elif e.response.status_code == 415:
                raise errors.Error("[%s.%s] - ThousandEyes reports that the supplied POST data is in the incorrect "
                                   "format. Detail: %s" % (__name__, self.__class__.__name__, e))
            elif e.response.status_code == 429:
                raise errors.Error("[%s.%s] - ThousandEyes reports that too many requests have been issued within "
                                   "a 1 minute period. Detail: %s" % (__name__, self.__class__.__name__, e))
            elif e.response.status_code == 500:
                raise errors.Error("[%s.%s] - ThousandEyes reports an internal server error. Contact support. "
                                   "Detail: %s" % (__name__, self.__class__.__name__, e))
            elif e.response.status_code == 503:
                raise errors.Error("[%s.%s] - ThousandEyes reports that it is currently in maintenance mode. "
                                   "Detail: %s" % (__name__, self.__class__.__name__, e))
        except requests.exceptions.ConnectionError as e:
            raise errors.Error("[%s.%s] - There was an error connecting to the ThousandEyes API URL specified. "
                               "Detail: %s" % (__name__, self.__class__.__name__, e))
        except requests.exceptions.Timeout as e:
            raise errors.Error("[%s.%s] - The connection to the ThousandEyes API timed out. "
                               "Detail: %s" % (__name__, self.__class__.__name__, e))
        except requests.exceptions.TooManyRedirects as e:
            raise errors.Error("[%s.%s] - The connection to the ThousandEyes API experienced too many redirects. "
                               "Detail: %s" % (__name__, self.__class__.__name__, e))
        else:
            return response


class NetworkTest(object):
    """A ThousandEyes network test.

    An entity for ThousandEyes network tests.
    """
    def __init__(self):
        self.id = 0
        self.name = ""
        self.enabled = False
        self.alerts_enabled = False
        self.protocol = "TCP"
        self.port = 80
        self.saved_event = 0
        self.server = ""
        self.url = ""
        self.bandwidth_measurements = False
        self.mtu_measurements = False
        self.network_measurements = False
        self.bgp_measurements = False
        self.interval = 0
        self.live_share = 0
        self.modified_date = datetime.now()
        self.modified_by = ""
        self.created_date = datetime.now()
        self.created_by = ""
        self.alert_rules = []
        self.groups = []
        self.agents = []
        self.bgp_monitors = []

    def to_json(self):
        """Convert relevant class attributes into a json format supported by Thousand Eyes.

        Creates a temporary object and populates it with current instance values.

        Returns:
            A json encoded string object.
        """
        class NewTest:
            pass

        new_test = NewTest()
        new_test.testName = self.name
        new_test.server = self.server
        new_test.interval = self.interval
        new_test.alertsEnabled = int(self.alerts_enabled)
        new_test.bandwidthMeasurements = int(self.bandwidth_measurements)
        new_test.bgpMeasurements = int(self.bgp_measurements)
        new_test.mtuMeasurements = int(self.mtu_measurements)
        new_test.protocol = self.protocol
        new_test.agents = self.agents
        if new_test.protocol == "TCP": new_test.port = self.port

        return json.dumps(new_test, default=lambda o: o.__dict__)

    def from_json(self, json_test):
        try:
            if "testId" in json_test: self.id = int(json_test["testId"])
            if "testName" in json_test: self.name = json_test["testName"]
            if "enabled" in json_test: self.enabled = bool(json_test["enabled"])
            if "alertsEnabled" in json_test: self.alerts_enabled = bool(json_test["alertsEnabled"])
            if "protocol" in json_test: self.protocol = json_test["protocol"]
            if "port" in json_test: self.port = int(json_test["port"])
            if "savedEvent" in json_test: self.saved_event = int(json_test["savedEvent"])
            if "server" in json_test: self.server = json_test["server"]
            if "url" in json_test: self.url = json_test["url"]
            if "bandwidthMeasurements" in json_test: self.bandwidth_measurements = bool(json_test["bandwidthMeasurements"])
            if "mtuMeasurements" in json_test: self.mtu_measurements = bool(json_test["mtuMeasurements"])
            if "networkMeasurements" in json_test: self.network_measurements = bool(json_test["networkMeasurements"])
            if "bgpMeasurements" in json_test: self.bgp_measurements = bool(json_test["bgpMeasurements"])
            if "interval" in json_test: self.interval = int(json_test["interval"])
            if "liveShare" in json_test: self.live_share = int(json_test["liveShare"])
            if "modifiedDate" in json_test: self.modified_date = datetime.strptime(json_test["modifiedDate"], "%Y-%m-%d %H:%M:%S")
            if "modifiedBy" in json_test: self.modified_by = json_test["modifiedBy"]
            if "createdDate" in json_test: self.created_date = datetime.strptime(json_test["createdDate"], "%Y-%m-%d %H:%M:%S")
            if "createdBy" in json_test: self.created_by = json_test["createdBy"]
        except KeyError as e:
            raise errors.Error("[%s.%s] - Key not found while parsing json. Detail: %s"
                               % (__name__, self.__class__.__name__, e))
        except ValueError as e:
            raise errors.Error("[%s.%s] - An error occurred while converting between json and NetworkTest types. "
                               "Detail: %s" % (__name__, self.__class__.__name__, e))


class Agent(object):
    """A ThousandEyes agent.

    An entity for ThousandEyes agents.
    """
    def __init__(self):
        self.id = 0
        self.name = ""
        self.type = ""
        self.county_id = ""
        self.location = ""
        self.prefix = ""
        self.enabled = False
        self.network = ""
        self.last_seen = datetime.now()
        self.state = ""
        self.utilisation = 0
        self.verify_ssl_certs = False
        self.keep_browser_cache = False
        self.ip_addresses = []
        self.public_ip_addresses = []
        self.groups = []

    def to_json(self):
        return json.dumps(self, default=lambda o: o.__dict__, sort_keys=True, indent=4)

    def from_json(self, json_agent):
        try:
            if "agentId" in json_agent: self.id = int(json_agent["agentId"])
            if "agentName" in json_agent: self.name = json_agent["agentName"]
            if "agentType" in json_agent: self.type = json_agent["agentType"]
            if "countryId" in json_agent: self.county_id = json_agent["countryId"]
            if "location" in json_agent: self.location = json_agent["location"]
            if "prefix" in json_agent: self.prefix = bool(json_agent["prefix"])
            if "enabled" in json_agent: self.enabled = json_agent["enabled"]
            if "network" in json_agent: self.network = json_agent["network"]
            if "lastSeen" in json_agent: self.last_seen = datetime.strptime(json_agent["lastSeen"], "%Y-%m-%d %H:%M:%S")
            if "agentState" in json_agent: self.state = json_agent["agentState"]
            if "utilization" in json_agent: self.utilisation = int(json_agent["utilization"])
            if "verifySslCertificates" in json_agent: self.verify_ssl_certs = bool(json_agent["verifySslCertificates"])
            if "keepBrowserCache" in json_agent: self.keep_browser_cache = bool(json_agent["keepBrowserCache"])
            if "ipAddresses" in json_agent:
                for ip in json_agent["ipAddresses"]:
                    self.ip_addresses.append(ip)
            if "publicIpAddresses" in json_agent:
                for ip in json_agent["publicIpAddresses"]:
                    self.public_ip_addresses.append(ip)
        except KeyError as e:
            raise errors.Error("[%s.%s] - Key not found while parsing json. Detail: %s"
                               % (__name__, self.__class__.__name__, e))
