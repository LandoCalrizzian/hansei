from kokuqe import api, config

def test_api_client():
    koku_cfg = config.get_config().get('koku', {})

    client = api.Client(username=koku_cfg.get('username'), password=koku_cfg.get('password'))
    assert client.token, 'No token provided after logging in'

    response = client.get_user()

    assert response.json()['username'] == koku_cfg['username'], (
        'Current user does not match expected \'admin\' user')

    response = client.server_status()
    assert len(response.json()) > 0, 'Server status is unavailable'
