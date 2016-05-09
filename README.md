SolarEyes
==========

Node and test synchronisation between SolarWinds and ThousandEyes.

© 2016 Carl G. Evans.

https://github.com/carlgevans/solareyes/

Written in Python.

##1. What is SolarEyes?

SolarEyes looks for nodes marked with a custom attribute in SolarWinds & creates them in Thousand Eyes as a test. If
nodes are removed from SolarWinds, the related test is also removed from ThousandEyes to keep the two systems in sync.

SolarWinds is treated as the master, so any test deletions on ThousandEyes will be ignored and re-added during the
next synchronisation.

##2. Libraries

Libraries are not included in the repository, so be sure to install them with command:

pip install -r requirements.txt

* Requests - HTTP requests library.
* ConfigParser - Config file library for reading settings.ini file.

##3. Installation

* Download the source.
* Download the library dependencies with pip (see above).
* Create a custom boolean attribute in SolarWinds and set the nodes that require synchronisation to 'True'.
* Configure the settings (username, password etc) for both the SolarWinds & ThousandEyes APIs.
* Configure the script to run on a schedule. Once per hour should be more than adequate.

##4. Notes

* RFC1918 addresses are currently ignored as ThousandEyes seems to reject them via the API,even though they
  can be created manually. Support for RFC1918 addresses would be useful for large private networks that are
  monitored by an Enterprise Agent with access to those networks.
* The requests library uses TLSv1.2 by default. In some cases the SolarWinds server might not support TLSv1.2 and this
  will be displayed in the event viewer as an SChannel error. See the following URL for details.

  http://stackoverflow.com/questions/14102416/python-requests-requests-exceptions-sslerror-errno-8-ssl-c504-eof-occurred

  The HTTPAdapter override solution was not working, but the nasty hack of connectionpool.py did.

* Only Thousand Eyes tests prefixed with the value contained in setting 'te_test_prefix' will be deleted. This is
  so that manually created tests are not affected by the synchronisation.

##5. License

SolarEyes has been released under the Apache 2.0 license. All contributors agree to transfer ownership of their
code to Carl G. Evans for release under this license.

###5.1 The Apache License

Copyright (c) 2016 Carl G. Evans

Licensed under the Apache License, Version 2.0 (the "License");
you may not use this file except in compliance with the License.
You may obtain a copy of the License at

    http://www.apache.org/licenses/LICENSE-2.0

Unless required by applicable law or agreed to in writing, software
distributed under the License is distributed on an "AS IS" BASIS,
WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
See the License for the specific language governing permissions and
limitations under the License.
