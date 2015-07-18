import logging

from kollaclient.i18n import _
from kollaclient.utils import read_etc_yaml
from kollaclient.utils import save_etc_yaml

from cliff.command import Command


class HostAdd(Command):
    "Host Add"

    log = logging.getLogger(__name__)

    def get_parser(self, prog_name):
        parser = super(HostAdd, self).get_parser(prog_name)
        parser.add_argument('hostname')
        parser.add_argument('ipaddress')
        # TODO(bmace) error if args missing
        return parser

    def take_action(self, parsed_args):
        hostname = parsed_args.hostname
        ipaddr = parsed_args.ipaddress
        contents = read_etc_yaml('hosts.yml')
        for host, hostdata in contents.items():
            if host == hostname:
                # TODO(bmace) fix message
                self.log.info(_("host already exists"))
                return
        hostEntry = {hostname: {'Services': '', 'IPAddr':
                     ipaddr, 'Zone': ''}}
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
        contents = read_etc_yaml('hosts.yml')
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
        contents = read_etc_yaml('hosts.yml')
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
