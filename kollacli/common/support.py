# Copyright(c) 2016, Oracle and/or its affiliates.  All Rights Reserved.
#
#    Licensed under the Apache License, Version 2.0 (the "License"); you may
#    not use this file except in compliance with the License. You may obtain
#    a copy of the License at
#
#         http://www.apache.org/licenses/LICENSE-2.0
#
#    Unless required by applicable law or agreed to in writing, software
#    distributed under the License is distributed on an "AS IS" BASIS, WITHOUT
#    WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied. See the
#    License for the specific language governing permissions and limitations
#    under the License.


import logging
import os
import tarfile
import tempfile
import traceback

import kollacli.i18n as u

from kollacli.common.inventory import Inventory
from kollacli.common.utils import get_kolla_etc
from kollacli.common.utils import get_kolla_home
from kollacli.common.utils import get_kolla_log_dir
from kollacli.common.utils import get_kollacli_etc
from kollacli.common.utils import run_cmd

LOG = logging.getLogger(__name__)


def dump():
    """Dumps configuration data for debugging

    Dumps most files in /etc/kolla and /usr/share/kolla into a
    tar file so be given to support / development to help with
    debugging problems.
    """
    try:
        msg = None
        return_code = 0
        kolla_home = get_kolla_home()
        kolla_logs = get_kolla_log_dir()
        kolla_ansible = os.path.join(kolla_home, 'ansible')
        kolla_docs = os.path.join(kolla_home, 'docs')
        kolla_etc = get_kolla_etc()
        kolla_config = os.path.join(kolla_etc, 'config')
        kolla_globals = os.path.join(kolla_etc, 'globals.yml')
        kollacli_etc = get_kollacli_etc().rstrip('/')
        ketc = 'kolla/etc/'
        kshare = 'kolla/share/'
        fd, dump_path = tempfile.mkstemp(prefix='kollacli_dump_',
                                         suffix='.tgz')
        os.close(fd)  # avoid fd leak
        with tarfile.open(dump_path, 'w:gz') as tar:
            # Can't blanket add kolla_home because the .ssh dir is
            # accessible by the kolla user only (not kolla group)
            tar.add(kolla_ansible,
                    arcname=kshare + os.path.basename(kolla_ansible))
            tar.add(kolla_docs,
                    arcname=kshare + os.path.basename(kolla_docs))

            # Can't blanket add kolla_etc because the passwords.yml
            # file is accessible by the kolla user only (not kolla group)
            tar.add(kolla_config,
                    arcname=ketc + os.path.basename(kolla_config))
            tar.add(kolla_globals,
                    arcname=ketc + os.path.basename(kolla_globals))
            tar.add(kollacli_etc,
                    arcname=ketc + os.path.basename(kollacli_etc))

            # add kolla log files
            if os.path.isdir(kolla_logs):
                tar.add(kolla_logs)

            # add output of various commands
            _add_cmd_info(tar)

        msg = u._LI('dump successful to {path}').format(path=dump_path)
        LOG.info(msg)

    except Exception:
        msg = (u._LI('dump failed: {reason}')
               .format(reason=traceback.format_exc()))
        LOG.error(msg)
        return_code = -1

    return return_code, msg


def _add_cmd_info(tar):
    # run all the kollacli list commands
    cmds = ['kollacli --version',
            'kollacli service listgroups',
            'kollacli service list',
            'kollacli group listservices',
            'kollacli group listhosts',
            'kollacli host list',
            'kollacli property list',
            'kollacli password list']

    # collect the json inventory output
    inventory = Inventory.load()
    inv_path = inventory.create_json_gen_file()
    cmds.append(inv_path)

    try:
        fd, path = tempfile.mkstemp(suffix='.tmp')
        os.close(fd)
        with open(path, 'w') as tmp_file:
            for cmd in cmds:
                err_msg, output = run_cmd(cmd, False)
                tmp_file.write('\n\n$ %s\n' % cmd)
                if err_msg:
                    tmp_file.write('Error message: %s\n' % err_msg)
                for line in output:
                    tmp_file.write(line + '\n')

        tar.add(path, arcname=os.path.join('kolla', 'cmds_output'))
    except Exception as e:
        raise e
    finally:
        if path:
            os.remove(path)
        inventory.remove_json_gen_file(inv_path)
    return
