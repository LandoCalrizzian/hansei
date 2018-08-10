"""
Global pytest plugins and hooks
"""

import os

from hansei import config as hansei_config

# This file should be reserved for command line args to modify the Hansei environment for a test run
# TODO: Use a plugin to move this functionality under the hansei folder
def pytest_addoption(parser):
    koku_group = parser.getgroup('koku')
    koku_group.addoption(
        "--koku-admin-username", action="store", default=os.environ.get('KOKU_SERVICE_ADMIN_USER'),
        help='Set the Koku Admin Username. DEFAULT: KOKU_SERVICE_ADMIN_USER')
    koku_group.addoption(
        "--koku-admin-password", action="store", default=os.environ.get('KOKU_SERVICE_ADMIN_PASSWORD'),
        help='Set the Koku Admin Password. DEFAULT: KOKU_SERVICE_ADMIN_PASSWORD')
    koku_group.addoption(
        "--koku-hostname", action="store", default=os.environ.get('KOKU_HOSTNAME'),
        help='Set the Koku service hostname. DEFAULT: KOKU_HOSTNAME')
    koku_group.addoption(
        "--koku-host-port", action="store", default=os.environ.get('KOKU_PORT'),
        help='Set the Koku service port. DEFAULT: KOKU_PORT')

def pytest_configure(config):
    koku_admin = config.getoption('koku_admin_username')
    koku_admin_pw = config.getoption('koku_admin_password')
    koku_hostname = config.getoption('koku_hostname')
    koku_host_port = config.getoption('koku_host_port')

    koku_config = hansei_config.get_config().get('koku', {})

    if koku_admin:
        koku_config['username'] = koku_admin

    if koku_admin_pw:
        koku_config['password'] = koku_admin_pw

    if koku_hostname:
        koku_config['hostname'] = koku_hostname

    if koku_host_port:
        koku_config['port'] = koku_host_port
