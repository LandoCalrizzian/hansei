"""
Global pytest plugins and hooks
"""
import os

from hansei import config as hansei_config, api as hansei_api
from requests.exceptions import HTTPError

def pytest_report_header(config):
    """Display the api version and git commit the koku server is running under"""

    koku_config = hansei_config.get_config().get('koku', {})

    report_header = ""

    try:
        client = hansei_api.Client(username=koku_config.get('username'), password=koku_config.get('password'))
        client.server_status()
        server_status = client.last_response.json()

        report_header = " - API Version: {}\n - Git Commit: {}".format(server_status['api_version'], server_status['commit'])

        if config.pluginmanager.hasplugin("junitxml") and hasattr(config, '_xml'):
            config._xml.add_global_property('Koku Server Id', server_status['server_id'])
            config._xml.add_global_property('Koku API Version', server_status['api_version'])
            config._xml.add_global_property('Koku Git Commit', server_status['commit'])
            config._xml.add_global_property('Koku Python Version', server_status['python_version'])

    except HTTPError:
        report_header = " - Unable to retrieve the server status"

    return "Koku Server Info:\n{}".format(report_header)

def pytest_addoption(parser):
    parser.addoption(
        "--koku-admin-username", action="store", default=os.environ.get('KOKU_SERVICE_ADMIN_USER'),
        help='Set the Koku Admin Username. DEFAULT: KOKU_SERVICE_ADMIN_USER')
    parser.addoption(
        "--koku-admin-password", action="store", default=os.environ.get('KOKU_SERVICE_ADMIN_PASSWORD'),
        help='Set the Koku Admin Password. DEFAULT: KOKU_SERVICE_ADMIN_PASSWORD')
    parser.addoption(
        "--koku-host-name", action="store", default=os.environ.get('KOKU_HOSTNAME'),
        help='Set the Koku service hostname. DEFAULT: KOKU_HOSTNAME')
    parser.addoption(
        "--koku-host-port", action="store", default=os.environ.get('KOKU_PORT'),
        help='Set the Koku service port. DEFAULT: KOKU_PORT')

def pytest_configure(config):
    koku_admin = config.getoption('koku_admin_username')
    koku_admin_pw = config.getoption('koku_admin_password')
    koku_hostname = config.getoption('koku_host_name')
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
