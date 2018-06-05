- As of change id: Id11cc1abcac6ac5b94176a1f17a8f5f82b6f00d5
removed all tests which expected remote systems
to be available / configured.  These tests should be
revived at some point using Tempest or something similar to run
more complete functional tests.

- To run a single functional test, you will need to setup these
environmental variables and the needed file structure:

export KOLLA_ETC=/tmp/kollaclitest/etc/kolla/
export KOLLA_HOME=/tmp/kollaclitest/usr/share/kolla-ansible/
export KOLLA_TOOLS_DIR=./tools/

./kolla_cli/tests/functional/functional_test_setup.sh

Then you can run a single test, for eg:

source .tox/functional/bin/activate
stestr run -n kolla_cli.tests.functional.test_deploy.TestFunctional.test_deploy
