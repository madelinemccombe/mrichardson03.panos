#!/usr/bin/python
# -*- coding: utf-8 -*-

#  Copyright 2020 Palo Alto Networks, Inc
#
#  Licensed under the Apache License, Version 2.0 (the "License");
#  you may not use this file except in compliance with the License.
#  You may obtain a copy of the License at
#
#      http://www.apache.org/licenses/LICENSE-2.0
#
#  Unless required by applicable law or agreed to in writing, software
#  distributed under the License is distributed on an "AS IS" BASIS,
#  WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
#  See the License for the specific language governing permissions and
#  limitations under the License.

from __future__ import absolute_import, division, print_function

__metaclass__ = type

DOCUMENTATION = """
---
module: panos_commit
short_description: Commit changes to a PAN-OS device.
description:
    - Commits changes to a PAN-OS device.
author:
    - Michael Richardson (@mrichardson03)
version_added: '1.0.0'
notes:
    - Panorama is supported.
    - Check mode is supported.
options:
    admins:
        description:
            - Commit only the changes made by the specified administrators.
        type: list
        elements: str
"""

EXAMPLES = """
- name: Commit firewall config
  panos_commit:

- name: commit changes by specified admins to firewall
  panos_commit:
    admins: ['admin1','admin2']
"""

RETURN = """
changed:
    description: A boolean value indicating if the task had to make changes.
    returned: always
    type: bool
msg:
    description: A string with an error message, if any.
    returned: failure, always
    type: str
stdout:
    description: output of the commit job as a JSON formatted string
    returned: always
    type: str
    sample: "{system: {app-release-date: 2017/05/01  15:09:12}}"
stdout_xml:
    description: output of the commit job as an XML formatted string
    returned: always
    type: str
    sample: "<response status=success><result><system><hostname>fw2</hostname>"
"""

import json
import xml.etree.ElementTree as ET

try:
    import xmltodict

    HAS_LIB = True
except ImportError:
    HAS_LIB = False

from ansible.module_utils.connection import ConnectionError
from ansible_collections.mrichardson03.panos.plugins.module_utils.panos import (
    PanOSAnsibleModule,
)


def parse_xml(xmlstr):
    return ET.fromstring(xmlstr)


def main():
    module = PanOSAnsibleModule(
        argument_spec=dict(admins=dict(type="list", elements="str")),
        supports_check_mode=True,
    )

    try:
        changes = parse_xml(module.connection.op("check pending-changes"))
        result = changes.find("./result").text

        if result == "no":
            module.exit_json(changed=False, msg="There are no changes to commit.")

        commit = parse_xml(module.connection.commit(admins=module.params["admins"]))
        job_id = commit.find("./result/job")

        if job_id is None:
            module.fail_json(msg="Could not find commit job.")
        else:
            job_id = job_id.text

        results_xml = module.connection.poll_for_job(job_id)
        results = parse_xml(results_xml)
        results_dict = xmltodict.parse(results_xml)

        commit_result = results.find("./result/job/result").text

        if commit_result == "OK":
            module.exit_json(
                changed=True, stdout=json.dumps(results_dict), stdout_xml=results_xml
            )
        else:
            module.fail_json(
                msg="Commit failed.",
                stdout=json.dumps(results_dict),
                stdout_xml=results_xml,
            )

    except ConnectionError as e:
        module.fail_json(msg="{0}".format(e))


if __name__ == "__main__":
    main()