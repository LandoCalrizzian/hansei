"""
Hansei Global pytest plugins and hooks
"""

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

