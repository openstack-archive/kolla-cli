import logging

from kollaclient.i18n import _
from kollaclient.sshutils import ssh_check_connect
from kollaclient.sshutils import ssh_check_keys
from kollaclient.sshutils import ssh_keygen
from kollaclient.utils import load_etc_yaml
from kollaclient.utils import save_etc_yaml

from cliff.command import Command


class HostAdd(Command):
    "Host Add"

    log = logging.getLogger(__name__)

    def get_parser(self, prog_name):
        parser = super(HostAdd, self).get_parser(prog_name)
        parser.add_argument('hostname')
        parser.add_argument('networkaddress')
        # TODO(bmace) error if args missing
        return parser

    def take_action(self, parsed_args):
        hostname = parsed_args.hostname
        networkAddress = parsed_args.networkaddress
        contents = load_etc_yaml('hosts.yml')
        for host, hostdata in contents.items():
            if host == hostname:
                # TODO(bmace) fix message
                self.log.info(_("host already exists"))
                return
        hostEntry = {hostname: {'Services': '', 'NetworkAddress':
                     networkAddress, 'Zone': ''}}
        contents.update(hostEntry)
        save_etc_yaml('hosts.yml', contents)


class HostRemove(Command):
    "Host Remove"

    log = logging.getLogger(__name__)

    def get_parser(self, prog_name):
        parser = super(HostRemove, self).get_parser(prog_name)
        parser.add_argument('hostname')
        # TODO(bmace) error if arg missing
        return parser

    def take_action(self, parsed_args):
        hostname = parsed_args.hostname
        contents = load_etc_yaml('hosts.yml')
        foundHost = False
        for host, hostdata in contents.items():
            if host == hostname:
                foundHost = True
        if foundHost:
            del contents[hostname]
        else:
            # TODO(bmace) fix message
            self.log.info("no host by name (" + hostname + ") found")
        save_etc_yaml('hosts.yml', contents)


class HostList(Command):
    "Host List"

    log = logging.getLogger(__name__)

    def take_action(self, parsed_args):
        self.log.info(_("host list"))
        contents = load_etc_yaml('hosts.yml')
        # TODO(bmace) fix output format
        for host, hostdata in contents.items():
            self.log.info(host)
            self.log.info(hostdata)


class HostSetzone(Command):
    "Host Setzone"

    log = logging.getLogger(__name__)

    def take_action(self, parsed_args):
        self.log.info(_("host setzone"))
        self.app.stdout.write(parsed_args)


class HostAddservice(Command):
    "Host Addservice"

    log = logging.getLogger(__name__)

    def take_action(self, parsed_args):
        self.log.info(_("host addservice"))
        self.app.stdout.write(parsed_args)


class HostRemoveservice(Command):
    "Host Removeservice"

    log = logging.getLogger(__name__)

    def take_action(self, parsed_args):
        self.log.info(_("host removeservice"))
        self.app.stdout.write(parsed_args)


class HostCheck(Command):
    "Host Check"

    log = logging.getLogger(__name__)

    def get_parser(self, prog_name):
        parser = super(HostCheck, self).get_parser(prog_name)
        parser.add_argument('hostname')
        # TODO(bmace) error if arg missing
        return parser

    def take_action(self, parsed_args):
        self.log.info(_("host check"))
        sshKeysExist = ssh_check_keys()
        if not sshKeysExist:
            ssh_keygen()
        hostname = parsed_args.hostname
        contents = load_etc_yaml('hosts.yml')
        hostFound = False
        for host, hostdata in contents.items():
            if host == hostname:
                # TODO(bmace) fix message
                hostFound = True
                networkAddress = hostdata['NetworkAddress']
                self.log.info(networkAddress)
                ssh_check_connect(networkAddress)

        if hostFound is False:
            self.log.info("no host by name (" + hostname + ") found")


class HostInstall(Command):
    "Host Install"

    log = logging.getLogger(__name__)

    def get_parser(self, prog_name):
        parser = super(HostInstall, self).get_parser(prog_name)
        parser.add_argument('hostname')
        # TODO(bmace) error if arg missing
        return parser

    def take_action(self, parsed_args):
        self.log.info(_("host install"))
        sshKeysExist = ssh_check_keys()
        if not sshKeysExist:
            ssh_keygen()
        hostname = parsed_args.hostname
        contents = load_etc_yaml('hosts.yml')
        hostFound = False
        for host, hostdata in contents.items():
            if host == hostname:
                # TODO(bmace) fix message
                hostFound = True
                networkAddress = hostdata['NetworkAddress']
                self.log.info(networkAddress)

        if hostFound is False:
            self.log.info("no host by name (" + hostname + ") found")
