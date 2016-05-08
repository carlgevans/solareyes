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

import thousandeyes
import solarwinds
import errors
import logging
import configparser
import functools

"""Synchronises nodes in Solarwinds with the path monitoring platform Thousand Eyes.

Nodes in Solarwinds that should be created as a test in Thousand Eyes should have a custom boolean property
(configurable in the settings file) set to True.
"""
__author__ = "Carl Evans"
__copyright__ = "Copyright 2016 Carl Evans"
__license__ = "Apache 2.0"
__title__ = "SolarEyes"
__version__ = "1.0"


class SolarEyes(object):
    """SolarEyes class.

    Handles the synchronisation between SolarWinds & ThousandEyes.

    Attributes:
        te_api: A ThousandEyes API instance.
        sw_api: A SolarWinds API instance.
        settings: A SolarEyesSettings instance.
        logger: A logging instance from the Python logging library.
    """
    def __init__(self, te_api=None, sw_api=None, settings=None, logger=None):
        if te_api is None or sw_api is None or settings is None or logger is None:
            raise errors.Error("[%s.%s] - You must provide instances of a Logger, SolarEyesSettings,"
                               "ThousandEyes & SolarWinds APIs." % (__name__, self.__class__.__name__))
        else:
            self.te_api = te_api
            self.sw_api = sw_api
            self.settings = settings
            self.logger = logger

    def check_apis(self):
        """Check the availability of both SolarWinds and ThousandEyes APIs.

        Returns:
            A boolean of True if both APIs are ready, or False if an error occurred.
        """
        if self.te_api.status() and self.sw_api.status():
            return True
        else:
            return False

    @functools.lru_cache(maxsize=32)
    def get_agent_ids(self):
        """Get a list of enterprise agent ids.

        Retrieve and filter a full list of agents for just the enterprise types and return a list of their ids.

        Returns:
            A list of integers representing all enterprise agent ids.
        """
        agent_ids = []
        agent_list = self.te_api.get_agents()

        for agent in agent_list:
            if agent.type == "Enterprise":
                agent_ids.append(agent.id)

        return agent_ids

    def get_se_tests(self, test_list):
        """Get a list of tests that were previously created with SolarEyes.

        Filter a full list of tests for those names starting with a specific prefix. This prefix
        is specified in the settings.ini file.

        Args:
            test_list: A list of thousandeyes.NetworkTest instances.

        Returns:
            A filtered list of thousandeyes.NetworkTest instances.
        """
        se_tests = []

        for test in test_list:
            if test.name[0:len(self.settings.te_test_prefix)] == self.settings.te_test_prefix:
                se_tests.append(test)

        return se_tests

    def get_path_nodes(self):
        """Get a list of nodes that have been marked as requiring path data.

        Returns:
            A list of node names and their IP addresses for those nodes requiring path data.
        """
        nodes = self.sw_api.query("SELECT NodeName, IPAddress FROM Orion.Nodes WHERE "
                                  "Nodes.CustomProperties.%s = TRUE" % self.settings.sw_custom_bool)

        node_dict = {}

        for node in nodes['results']:
            node_dict[node['IPAddress']] = node['NodeName']

        return node_dict

    def create_test(self, test_name=None, test_server=None):
        """Create a single test with defaults taken from settings.ini and from passed values.

        Args:
            test_name: The name of the test as displayed in the ThousandEyes web interface.
            test_server: The IP address that will be tested in ThousandEyes.

        Returns:
            A boolean of True if the creation was successful or False if an error occurred.
        """
        if test_name is None or test_server is None:
            raise errors.Error("[%s.%s] - You must provide a test name and server."
                               % (__name__, self.__class__.__name__))
        else:
            test = thousandeyes.NetworkTest()
            test.name = self.settings.te_test_prefix + " " + test_name
            test.server = test_server
            test.alerts_enabled = bool(self.settings.te_test_alerts)
            test.bandwidth_measurements = False
            test.mtu_measurements = True
            test.network_measurements = True
            test.bgp_measurements = True
            test.protocol = self.settings.te_test_protocol
            test.port = int(self.settings.te_test_port)
            test.interval = int(self.settings.te_test_interval)

            for agent_id in self.get_agent_ids():
                test.agents.append({"agentId": agent_id})

            if self.te_api.create_network_test(test):
                return True
            else:
                return False

    def create_tests(self, path_nodes, se_tests):
        """Create any new tests from a passed list of SolarWinds nodes and current ThousandEyes tests.

        Args:
            path_nodes: A dictionary containing the current list of IP addresses that require path data.
            se_tests: A current list of ThousandEyes tests that were created with SolarEyes.

        Returns:
            A boolean of True if the process was successful or False if an error occurred.
        """
        ignore_list = []

        for test in se_tests:
            if test.server in path_nodes:
                    ignore_list.append(test.server)

        for ip, name in path_nodes.items():
            if ip not in ignore_list:
                self.logger.debug("[%s] - Attempting to create test %s (%s) on ThousandEyes."
                                  % (self.__class__.__name__, name, ip))

                if self.create_test(name, ip):
                    self.logger.info("[%s] - ThousandEyes test %s (%s) was created."
                                     % (self.__class__.__name__, name, ip))
                else:
                    self.logger.error("[%s] - An error occurred while attempting to create ThousandEyes test %s (%s)."
                                      % (self.__class__.__name__, name, ip))
            else:
                self.logger.debug("[%s] - %s (%s) was already present on ThousandEyes."
                                  % (self.__class__.__name__, name, ip))

    def delete_orphaned_tests(self, path_nodes, se_tests):
        """Delete tests on ThousandEyes that don't have a matching node in SolarWinds.

        Args:
            path_nodes: A dictionary containing the current list of IP addresses that require path data.
            se_tests: A current list of ThousandEyes tests that were created with SolarEyes.

        Returns:
            A boolean of True if the deletion was successful or False if an error occurred.
        """
        for se_test in se_tests:
            if se_test.server not in path_nodes:
                if self.te_api.delete_network_test(se_test.id):
                    self.logger.info("[%s] - ThousandEyes test %s was deleted."
                                     % (self.__class__.__name__, se_test.name))
                else:
                    self.logger.error("[%s] - An error occurred while attempting to delete ThousandEyes test %s."
                                      % (self.__class__.__name__, se_test.name))
            else:
                self.logger.debug("[%s] - Thousand Eyes test %s (%s) is still present as a node in SolarWinds. "
                                  "Deletion not required." % (self.__class__.__name__, se_test.name, se_test.server))

    def sync(self):
        """Perform a synchronisation between SolarWinds and ThousandEyes.

        Returns:
            A boolean of True if the synchronisation was successful, or False if an error occurred.
        """
        if self.check_apis():
            # Get current lists from both SolarWinds & ThousandEyes API.
            se_tests = self.get_se_tests(self.te_api.get_network_tests())
            path_nodes = self.get_path_nodes()

            # Delete any tests on ThousandEyes that don't have a node on SolarWinds.
            self.delete_orphaned_tests(path_nodes, se_tests)

            # Create any tests for new nodes on SolarWinds.
            self.create_tests(path_nodes, se_tests)

            return True
        else:
            return False


class SolarEyesSettings(object):
    """All external settings required by the SolarEyes class.

    Attributes:
        sw_custom_bool: A string containing the base API url such as https://api.thousandeyes.com.
        te_test_protocol: A string containing the ThousandEyes default test protocol.
        te_test_port: A string containing the ThousandEyes default test port.
        te_test_alerts: A string containing the ThousandEyes default test alert requirements.
        te_test_interval: A string containing the ThousandEyes default test interval.
        te_test_prefix: A string containing the ThousandEyes default test name prefix.
    """
    def __init__(self, sw_custom_bool=None, te_test_protocol=None, te_test_port=None,
                 te_test_alerts=None, te_test_interval=None, te_test_prefix=None):

        if sw_custom_bool is None or te_test_protocol is None or te_test_port is None \
                or te_test_alerts is None or te_test_interval is None or te_test_prefix is None:
                    raise errors.Error("[%s.%s] - You must provide all required settings to SolarEyesSettings."
                                       % (__name__, self.__class__.__name__))
        else:
            self.sw_custom_bool = sw_custom_bool
            self.te_test_protocol = te_test_protocol
            self.te_test_port = te_test_port
            self.te_test_alerts = te_test_alerts
            self.te_test_interval = te_test_interval
            self.te_test_prefix = te_test_prefix


def main():
    # Read settings file.
    config = configparser.ConfigParser()
    config.read('settings.ini')
    settings = config['Settings']

    # Configure logging.
    logging.basicConfig(level=logging.DEBUG,
                        filename=settings['log_file'], filemode=settings['log_mode'],
                        format='%(asctime)s %(levelname)s %(message)s')

    try:
        # Create various instances required by the SolarEyes constructor.
        te_api_request = thousandeyes.ApiRequest(settings['te_api'], settings['te_auth_email'], settings['te_auth_token'])
        te_api = thousandeyes.Api(te_api_request)
        sw_api = solarwinds.Api(settings['sw_api'], settings['sw_username'], settings['sw_password'])
        se_settings = SolarEyesSettings(settings['sw_custom_bool'],
                                        settings['te_test_protocol'],
                                        settings['te_test_port'],
                                        settings['te_test_alerts'],
                                        settings['te_test_interval'],
                                        settings['te_test_prefix'])

        # Pass the above API and settings instances to the constructor of SolarEyes.
        solareyes = SolarEyes(te_api, sw_api, se_settings, logging)
    except errors.Error as error:
        logging.error(error)
    else:
        try:
            # Run synchronisation.
            if solareyes.sync():
                logging.info("[%s] - Synchronisation successful." % __name__)
            else:
                logging.error("[%s] - There was a problem during synchronisation."
                              % __name__)
        except errors.Error as error:
            logging.error(error)

# Only execute the main script if passed to an interpreter. Do not execute if imported.
if __name__ == "__main__":
    main()
